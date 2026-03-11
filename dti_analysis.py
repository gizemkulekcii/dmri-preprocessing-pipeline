import os
import glob
import numpy as np
import nibabel as nib
from dipy.io.image import load_nifti
from dipy.io.gradients import read_bvals_bvecs
from dipy.core.gradients import gradient_table
import dipy.reconst.dti as dti
import dipy.data as dpd
import dipy.denoise.noise_estimate as ne

def DTI(data, gtab):

    tenmodel = dti.TensorModel(gtab)
    tenfit = tenmodel.fit(data)

    return tenfit.fa , tenfit.md, tenfit.ad , tenfit.rd 

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

        # Ensure output directory exists
        os.makedirs(dti_path, exist_ok=True)

        # Load DWI image
        data_path = os.path.join(skull_stripped_path, f"{subject_id}_{session_id}_skull_stripped_dwi.nii.gz")
        denoised_data_path = os.path.join(patch2self_path, f"{subject_id}_{session_id}_acq-b1000_dwi_denoised_patch2self.nii.gz")

        if not os.path.exists(data_path) or not os.path.exists(denoised_data_path):
            print(f"ERROR: Missing data for {subject_id}, skipping.")
            continue

        data, affine, img = load_nifti(data_path, return_img=True)
        denoised_data, denoised_affine, denoised_img = load_nifti(denoised_data_path, return_img=True)
        
        print(f"Data range (original): min={np.min(data)}, max={np.max(data)}")
        print(f"Data range (denoised): min={np.min(denoised_data)}, max={np.max(denoised_data)}")
        print(f"Negative values count (original): {np.sum((data < 0))}")
        print(f"Negative values count (denoised): {np.sum((denoised_data < 0))}")
        #data[data < 0] = 0
        #denoised_data[denoised_data < 0] = 0

        # Define b-values and b-vectors file paths
        bval_fname = os.path.join(subject_id, session_id, "dwi", f"{subject_id}_{session_id}_acq-b1000_dir-AP_dwi.bval")
        bvec_fname = os.path.join(eddy_path,f"{subject_id}_{session_id}_eddy_corrected.eddy_rotated_bvecs")

        # Check if the b-val and b-vec files exist
        if not os.path.exists(bval_fname) or not os.path.exists(bvec_fname):
            print(f"Error: Missing bval or bvec file for {subject_id} in {session_id}. Skipping.")
            continue
        
        # Load b-values and b-vectors
        bvals, bvecs = read_bvals_bvecs(bval_fname, bvec_fname)
        #print("B-values:", np.unique(bvals))
        #print("First 5 B-vectors:\n", bvecs[:5])
        gtab = gradient_table(bvals, bvecs=bvecs)
        
        # Compute DTI maps for original data
        fa, md, ad, rd = DTI(data, gtab)
        # Save as NIfTI files
        nib.save(nib.Nifti1Image(fa.astype(np.float32), affine), os.path.join(dti_path, f"{subject_id}_{session_id}_FA.nii.gz"))
        nib.save(nib.Nifti1Image(md.astype(np.float32), affine), os.path.join(dti_path, f"{subject_id}_{session_id}_MD.nii.gz"))
        nib.save(nib.Nifti1Image(ad.astype(np.float32), affine), os.path.join(dti_path, f"{subject_id}_{session_id}_AD.nii.gz"))
        nib.save(nib.Nifti1Image(rd.astype(np.float32), affine), os.path.join(dti_path, f"{subject_id}_{session_id}_RD.nii.gz"))
        
        # Compute DTI maps for denoised data
        d_fa, d_md, d_ad, d_rd = DTI(data, gtab)
        # Save as NIfTI files
        nib.save(nib.Nifti1Image(fa.astype(np.float32), affine), os.path.join(dti_path, f"{subject_id}_{session_id}_FA_denoised.nii.gz"))
        nib.save(nib.Nifti1Image(md.astype(np.float32), affine), os.path.join(dti_path, f"{subject_id}_{session_id}_MD_denoised.nii.gz"))
        nib.save(nib.Nifti1Image(ad.astype(np.float32), affine), os.path.join(dti_path, f"{subject_id}_{session_id}_AD_denoised.nii.gz"))
        nib.save(nib.Nifti1Image(rd.astype(np.float32), affine), os.path.join(dti_path, f"{subject_id}_{session_id}_RD_denoised.nii.gz"))
    