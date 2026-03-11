import os
import glob
import numpy as np
import subprocess
import nibabel as nib
from dipy.io.image import load_nifti, save_nifti

def compute_mean_b0(dwi_data, b0_threshold=50): 
    #Compute the mean b0 image by averaging all volumes with b < b0_threshold.
    return np.mean(dwi_data[..., :b0_threshold], axis=-1)

# Loop through each subject directory
for subject_id in glob.glob("sub*"): # Find all subject directories
    for ses_dir in glob.glob(os.path.join(subject_id, "ses-*")):
        session_id = os.path.basename(ses_dir)
        print(f"Processing subject {subject_id} in {session_id}")
        
        # Define paths 
        eddy_path = os.path.join("derivatives","eddy_output",subject_id, session_id)
        skull_stripped_path = os.path.join("derivatives","skull_stripped_output",subject_id, session_id)

        # Ensure output directory exists
        os.makedirs(skull_stripped_path, exist_ok=True)

        # Load DWI image
        data_path = os.path.join(eddy_path, f"{subject_id}_{session_id}_eddy_corrected.nii.gz")
        data, affine, img = load_nifti(data_path, return_img=True)

        mean_b0 = compute_mean_b0(data)
        mean_b0_path = os.path.join(skull_stripped_path, f"{subject_id}_{session_id}_mean_b0.nii.gz")
        save_nifti(mean_b0_path, mean_b0, affine)
        
        masked_data_path =  os.path.join(skull_stripped_path, f"{subject_id}_{session_id}_bet_brain.nii.gz")
        mask_path =  os.path.join(skull_stripped_path, f"{subject_id}_{session_id}_bet_brain_mask.nii.gz")
        
        # Run BET command with options
        bet_cmd = f"bet {mean_b0_path} {masked_data_path} -m -f 0.3 -R"

        # Execute the command
        subprocess.run(bet_cmd, shell=True, check=True)
        print(f"BET completed. Skull-stripped image saved as: {masked_data_path}")
        print(f"Brain mask saved as: {mask_path}")

        # Load the brain mask
        brain_mask_nii = nib.load(mask_path)
        brain_mask = brain_mask_nii.get_fdata()

        # Ensure mask is binary (0s and 1s only)
        brain_mask = (brain_mask > 0).astype(np.float32)

        # Apply the mask to the **original 4D DWI data**
        masked_data = data * brain_mask[..., np.newaxis] 

        # Save the skull-stripped DWI
        skull_stripped_dwi_path = os.path.join(skull_stripped_path, f"{subject_id}_{session_id}_skull_stripped_dwi.nii.gz")
        save_nifti(skull_stripped_dwi_path, masked_data, affine)

        print(f"Skull-stripped DWI saved: {skull_stripped_dwi_path}")