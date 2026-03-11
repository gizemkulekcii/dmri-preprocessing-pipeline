import os
import glob
import numpy as np
import subprocess
import nibabel as nib
from dipy.denoise.patch2self import patch2self
from dipy.io.image import load_nifti, save_nifti
from dipy.io.gradients import read_bvals_bvecs

# Loop through each subject directory
for subject_id in glob.glob("sub*"): # Find all subject directories
    for ses_dir in glob.glob(os.path.join(subject_id, "ses-*")):
        session_id = os.path.basename(ses_dir)
        print(f"Processing subject {subject_id} in {session_id}")
        
        # Define paths 
        eddy_path = os.path.join("derivatives","eddy_output",subject_id, session_id)
        skull_stripped_path = os.path.join("derivatives","skull_stripped_output",subject_id, session_id)
        patch2self_path= os.path.join("derivatives","denoise_patch2self_output",subject_id, session_id)

        # Ensure output directories exist
        os.makedirs(patch2self_path, exist_ok=True)
        
        # Load DWI image
        skulstripped_data_path = os.path.join(skull_stripped_path, f"{subject_id}_{session_id}_skull_stripped_dwi.nii.gz")
        skulstripped_data, skulstripped_affine, skulstripped_img = load_nifti(skulstripped_data_path, return_img=True)
        
        if not os.path.exists(skulstripped_data_path):
            print(f"Error: Skull stripped dwi file not found. Skipping {subject_id} in {session_id}.")
            continue

        # Define b-values and b-vectors file paths
        bval_fname = os.path.join(subject_id, session_id, "dwi", f"{subject_id}_{session_id}_acq-b1000_dir-AP_dwi.bval")
        bvec_fname = os.path.join(eddy_path,f"{subject_id}_{session_id}_eddy_corrected.eddy_rotated_bvecs")
        
        # Check if bval and bvec files exist
        if not os.path.exists(bval_fname) or not os.path.exists(bvec_fname):
            print(f"Error: Missing bval or bvec file for {subject_id} in {session_id}. Skipping.")
            continue

        # Load b-values and b-vectors
        bvals, bvecs = read_bvals_bvecs(bval_fname, bvec_fname)

        # Apply Patch2Self denoising to the skull-stripped data
        print(f"Applying Patch2Self denoising for {subject_id} in {session_id}")
        denoised_arr = patch2self(skulstripped_data, bvals, model="ridge", shift_intensity=True, b0_threshold=50,  alpha=2)

        # Save denoised output
        output_file = os.path.join(patch2self_path, f"{subject_id}_{session_id}_acq-b1000_dwi_denoised_patch2self.nii.gz")
        save_nifti(output_file, denoised_arr, skulstripped_affine)
        print(f"Saved denoised image for {subject_id} in {session_id} : {output_file}")