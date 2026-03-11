import nibabel as nib
import numpy as np
import os
from dipy.io.image import load_nifti

def create_mask(image_path, intensity):

    # Load the NIfTI image using nibabel 
    mask_data, mask_affine, mask_img = load_nifti(image_path, return_img=True)

    # Create the white matter mask 
    mask = np.isin(mask_data, intensity).astype(np.uint8)
    
    print("The mask created.  Shape:", mask.shape)

    mask_nifti = nib.Nifti1Image(mask, mask_affine, mask_img.header)

    return mask, mask_affine, mask_nifti

def midline(data, affine, img):
    header = img.header
    midline = data.shape[0] // 2

    # Create masks
    left_mask = np.zeros_like(data)
    right_mask = np.zeros_like(data)

    # Assign hemispheres
    left_mask[midline:, :, :] = data[midline:, :, :]
    right_mask[:midline, :, :] = data[:midline, :, :]
    
    # Save the masks as NIfTI files
    left_img = nib.Nifti1Image(left_mask, affine, header)
    right_img = nib.Nifti1Image(right_mask, affine, header)

    print("Left and right hemisphere masks created.")
    return left_mask, right_mask, left_img, right_img


'''
Juelich-maxprob-thr25-2mm:
<label index="16" x="119" y="110" z="53">GM Hippocampus cornu ammonis L</label>
<label index="17" x="56" y="111" z="53">GM Hippocampus cornu ammonis R</label>
<label index="18" x="115" y="121" z="35">GM Hippocampus entorhinal cortex L</label>
<label index="19" x="64" y="125" z="34">GM Hippocampus entorhinal cortex R</label>
<label index="20" x="119" y="109" z="53">GM Hippocampus dentate gyrus L</label>
<label index="21" x="58" y="110" z="54">GM Hippocampus dentate gyrus R</label>
<label index="22" x="107" y="117" z="50">GM Hippocampus hippocampal-amygdaloid transition area L</label>
<label index="23" x="71" y="117" z="51">GM Hippocampus hippocampal-amygdaloid transition area R</label>
<label index="24" x="112" y="115" z="43">GM Hippocampus subiculum L</label>
<label index="25" x="64" y="107" z="54">GM Hippocampus subiculum R</label>

'''

image_path = "Juelich-maxprob-thr25-2mm.nii.gz"  
left_intensity = [16,18,20,22,24] 
right_intensity = [17,19,21,22,25] 
# Create the mask
left_mask, left_affine, left_img = create_mask(image_path, left_intensity)
right_mask, right_affine, right_img = create_mask(image_path, right_intensity)

output_path_left = os.path.join("derivatives","mask_output","left_hippocampus_mask_juelich.nii")
output_path_right = os.path.join("derivatives","mask_output","right_hippocampus_mask_juleich.nii")

nib.save(left_img, output_path_left)
nib.save(right_img, output_path_right)