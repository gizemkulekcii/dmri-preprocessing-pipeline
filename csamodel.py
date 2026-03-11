import os
import glob
from dipy.viz import actor, has_fury, window
import matplotlib.pyplot as plt
from dipy.core.gradients import gradient_table
from dipy.data import default_sphere
from dipy.direction import peaks_from_model
from dipy.io.gradients import read_bvals_bvecs
from dipy.io.image import load_nifti
from dipy.reconst.shm import CsaOdfModel

def csa_model(data, mask, gtab, csa_path, subject_id, session_id):
    csa_model = CsaOdfModel(gtab = gtab, sh_order_max = 6) # CsaOdfModel for direction estimation
    # Extracts the main diffusion directions from the ODFs across the brain, applying a peak threshold and angular separation to ensure valid fiber directions.
    csa_peaks = peaks_from_model(model = csa_model, data = data, sphere = default_sphere,
                                     relative_peak_threshold=.8,
                                     min_separation_angle=45,
                                     mask=mask )
    # Enables/disables interactive visualization
    interactive = False

    if has_fury:
        scene = window.Scene()
        scene.add(actor.peak_slicer(csa_peaks.peak_dirs, peaks_values=csa_peaks.peak_values, colors=None))

        window.record(scene=scene, out_path=os.path.join(csa_path, f"{subject_id}_{session_id}_csa_direction_field.png"), size=(900, 900))

        if interactive:
            window.show(scene, size=(800, 800))
        
        sli = csa_peaks.gfa.shape[2] // 2
        plt.figure("GFA")
        plt.subplot(1, 2, 1).set_axis_off()
        plt.imshow(csa_peaks.gfa[:, :, sli].T, cmap="gray", origin="lower")

        plt.subplot(1, 2, 2).set_axis_off()
        plt.imshow((csa_peaks.gfa[:, :, sli] > 0.25).T, cmap="gray", origin="lower")

        plt.savefig(os.path.join(csa_path, f"{subject_id}_{session_id}_gfa_tracking_mask.png"))

# Loop through each subject directory
for subject_id in glob.glob("sub*"): # Find all subject directories
    for ses_dir in glob.glob(os.path.join(subject_id, "ses-*")):
        session_id = os.path.basename(ses_dir)
        print(f"Processing subject {subject_id} in {session_id}")
        
        # Define paths
        eddy_path = os.path.join("derivatives","eddy_output",subject_id, session_id)
        patch2self_path= os.path.join("derivatives","denoise_patch2self_output",subject_id, session_id)
        skull_stripped_path = os.path.join("derivatives","skull_stripped_output",subject_id, session_id)
        dti_path = os.path.join("derivatives","dti_output",subject_id, session_id)
        csa_path = os.path.join("derivatives","csa_output",subject_id, session_id)
        
        # Ensure output directory exists
        os.makedirs(csa_path, exist_ok=True)

        # Load DWI image
        data_path = os.path.join(skull_stripped_path, f"{subject_id}_{session_id}_skull_stripped_dwi.nii.gz")
        denoised_data_path = os.path.join(patch2self_path, f"{subject_id}_{session_id}_acq-b1000_dwi_denoised_patch2self.nii.gz")
        mask_path= os.path.join(skull_stripped_path, f"{subject_id}_{session_id}_bet_brain_mask.nii.gz")

        if not os.path.exists(data_path) or not os.path.exists(denoised_data_path):
            print(f"ERROR: Missing data for {subject_id}, skipping.")
            continue

        data, affine, img = load_nifti(data_path, return_img=True)
        denoised_data, denoised_affine, denoised_img = load_nifti(denoised_data_path, return_img=True)
        mask, m_affine, m_img = load_nifti(mask_path, return_img=True)
        mask[mask< 0] = 0
        
        # Define paths to b-values and b-vectors files
        bval_fname = os.path.join(subject_id, session_id, "dwi", f"{subject_id}_{session_id}_acq-b1000_dir-AP_dwi.bval")
        bvec_fname = os.path.join(eddy_path,f"{subject_id}_{session_id}_eddy_corrected.eddy_rotated_bvecs")
        # Load the b-values and b-vectors
        bvals, bvecs = read_bvals_bvecs(bval_fname, bvec_fname)
        gtab = gradient_table(bvals =bvals, bvecs=bvecs)

        #print("Gradient table bvals:", gtab.bvals)
        #print("Gradient table bvecs:", gtab.bvecs)
        #print("Gradient table summary:", gtab.info)

        csa_model(data, mask, gtab, csa_path, subject_id, session_id)
     


