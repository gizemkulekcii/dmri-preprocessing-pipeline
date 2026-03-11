import os
import glob
from dipy.io.image import load_nifti
from dipy.io import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from scipy.ndimage import binary_dilation, binary_erosion
from dipy.tracking import utils
from dipy.tracking.utils import length
from dipy.reconst.shm import CsaOdfModel
from dipy.direction import  peaks_from_model
from dipy.data import default_sphere
from dipy.tracking.stopping_criterion import ThresholdStoppingCriterion
from dipy.reconst.csdeconv import ConstrainedSphericalDeconvModel, auto_response_ssst
from dipy.direction import ProbabilisticDirectionGetter
from dipy.tracking.local_tracking import LocalTracking
from dipy.tracking.streamline import Streamlines, cluster_confidence
from dipy.io.stateful_tractogram import StatefulTractogram, Space
from dipy.io.streamline import save_trk

def refine_mask(mask, iterations=2): 
    '''Applies dilation followed by erosion to refine binary masks.'''
    dilated_mask = binary_dilation(mask, iterations=iterations)
    refined_mask = binary_erosion(dilated_mask, iterations=iterations)
    return refined_mask.astype(bool)

def seedGeneration(mask_data, dwi_affine, density):
    ''' Generates seeding points for tractography within a given mask.'''
    seeds  = utils.seeds_from_mask(mask= mask_data, affine= dwi_affine, density=density)
    return seeds

def stoppingCriterion_csa(gtab, dwi_data, mask_data): 
    ''' Creates a stopping criterion based on Generalized Fractional Anisotropy (GFA) from CsaOdfModel.'''
    # The CsaOdfModel estimates the fiber orientation distribution function (ODF) from the diffusion data, using spherical harmonics of order 6 for detailed modeling.
    csa_model = CsaOdfModel(gtab = gtab, sh_order_max= 6) # CsaOdfModel for direction estimation
    # Extracts the main diffusion directions from the ODFs across the brain, applying a peak threshold and angular separation to ensure valid fiber directions.
    csa_peaks = peaks_from_model(model = csa_model, data = dwi_data, sphere = default_sphere,
                                      relative_peak_threshold=.8,
                                      min_separation_angle=45,
                                      mask=mask_data)
    print("GFA shape:", csa_peaks.gfa.shape if csa_peaks.gfa is not None else "None")
    
    stopping_criterion = ThresholdStoppingCriterion(metric_map = csa_peaks.gfa, threshold =.15)
    return stopping_criterion

def probabilisticDirectionGetter_csd(gtab, dwi_data, mask_data): 
    ''' Computes a probabilistic direction getter using Constrained Spherical Deconvolution (CSD)'''
    # Constrained Spherical Deconvolution (CSD) is performed to estimate the fiber orientation distribution with higher accuracy by deconvolving the signal. 
    response, ratio = auto_response_ssst(gtab=gtab, data=dwi_data, roi_radii=10, fa_thr=0.3) # Estimates the response function from the data
    csd_model = ConstrainedSphericalDeconvModel(gtab=gtab, response=response, sh_order_max=6) # Fits the CSD model to the DWI data.
    csd_fit = csd_model.fit(data=dwi_data, mask=mask_data)
    # The ProbabilisticDirectionGetter is initialized with spherical harmonic coefficients from the CSD fit. It probabilistically samples fiber directions during tractography, allowing for modeling of crossing fibers.
    prob_dg = ProbabilisticDirectionGetter.from_shcoeff(csd_fit.shm_coeff, max_angle=45., sphere=default_sphere)
    return prob_dg


def streamlinesGen(directionGetter, stopping_criterion, seeds, dwi_affine): 
    '''Generates streamlines using probabilistic tractography.'''
    streamlines_generator = LocalTracking(direction_getter = directionGetter, stopping_criterion = stopping_criterion, seeds = seeds, affine = dwi_affine, step_size= 0.5) 
    # The generated streamlines are stored in a Streamlines object, and a StatefulTractogram is created to keep track of the streamlines in a specific coordinate space (RASMM - Right-Anterior-Superior in millimeters).
    streamlines = Streamlines(streamlines_generator)
    sft = StatefulTractogram(streamlines, dwi_img, Space.RASMM) # Convert to StatefulTractogram
    return streamlines, sft

# Loop through each subject directory
for subject_id in glob.glob("sub*"): # Find all subject directories
    for ses_dir in glob.glob(os.path.join(subject_id, "ses-*")): # Loop through session directories
        session_id = os.path.basename(ses_dir) # Extract session ID
        
        # Define paths to various outputs 
        eddy_path = os.path.join("derivatives","eddy_output",subject_id, session_id)
        patch2self_path= os.path.join("derivatives","denoise_patch2self_output",subject_id, session_id)
        skull_stripped_path = os.path.join("derivatives","skull_stripped_output",subject_id, session_id)
        dti_path = os.path.join("derivatives","dti_output",subject_id, session_id)
        csa_path = os.path.join("derivatives","csa_output",subject_id, session_id)
        hmask_path = os.path.join("derivatives","hmask_output",subject_id, session_id)
        tracking_path = os.path.join("derivatives","tracking_output",subject_id, session_id)
        
        # Ensure output directories exist
        os.makedirs(tracking_path, exist_ok=True)
        
        # Load DWI and FA data (both skull-stripped)
        data_path = os.path.join(skull_stripped_path, f"{subject_id}_{session_id}_skull_stripped_dwi.nii.gz")
        #data_path = os.path.join(patch2self_path, f"{subject_id}_{session_id}_acq-b1000_dwi_denoised_patch2self.nii.gz")
        dwi_data, dwi_affine, dwi_img = load_nifti(data_path, return_img=True)
        
        fa_path =  os.path.join(dti_path, f"{subject_id}_{session_id}_FA.nii.gz")
        fa_data, fa_affine, fa_img = load_nifti(fa_path, return_img=True)

        # Load the b-values and b-vectors
        bval_fname = os.path.join(subject_id, session_id, "dwi", f"{subject_id}_{session_id}_acq-b1000_dir-AP_dwi.bval")
        bvec_fname = os.path.join(eddy_path,f"{subject_id}_{session_id}_eddy_corrected.eddy_rotated_bvecs")
        bvals, bvecs = read_bvals_bvecs(bval_fname, bvec_fname) # Read bvals and bvecs and create gradient table
        gtab = gradient_table(bvals=bvals, bvecs=bvecs) # Creates a gradient table for diffusion modeling.
        
        # Load the brain mask
        mask_fname= os.path.join(skull_stripped_path, f"{subject_id}_{session_id}_bet_brain_mask.nii.gz")
        mask, mask_affine, mask_img = load_nifti(mask_fname, return_img=True)
        mask[mask < 0] = 0 # Ensure binary mask
        mask = mask.astype(bool)
        mask = refine_mask(mask) # Refine the mask

        print("DWI Data Shape:", dwi_data.shape)
        print("FA Data Shape:", fa_data.shape)
        print("Mask Shape:", mask.shape)
        print("Affine Transform:\n", dwi_affine)

        # Generate seed points for tractography
        print("Generating Seeds...")
        seed_mask= fa_data > 0.2  # Threshold FA data to create seed mask
        seeds = seedGeneration(seed_mask, dwi_affine,[1, 1, 1]) # Generate seeds 
    
        # Compute stopping criteria for tractography
        print("Generating Threshold Stopping Criterion ...")
        stopping_criterion = stoppingCriterion_csa(gtab, dwi_data, mask)
        
        # Generate probabilistic direction getter
        print("Generating Probabilistic direction getter ...")
        probabilistic_direction_getter = probabilisticDirectionGetter_csd(gtab, dwi_data, mask)

        # Generate streamlines from IC seeds
        print("Generating Left and Right Streamlines...")
        streams, sft = streamlinesGen(probabilistic_direction_getter, stopping_criterion, seeds, dwi_affine)
        
        # Save the streamlines to a .trk file
        save_trk(sft, os.path.join(tracking_path, f"{subject_id}_streams.trk")) 
        print(f"Saved  streamlines for {subject_id}/{session_id}!")
