A set of scripts for processing diffusion MRI (dMRI) data, including motion correction, brain masking, denoising, diffusion tensor imaging (DTI) analysis, compartment modeling, and tractography. Each script is designed to be run independently or as part of a complete pipeline. 

Dependencies: Python, FSL(for distortion and motion correction), DIPY (for tensor fitting, denoising, and tractography)

1. distortion_motion_correction.sh : This script applies distortion and motion correction to diffusion MRI data. It corrects for artifacts caused by head motion and susceptibility-induced distortions.
2. brain_mask.py: Generates a brain mask from the diffusion MRI data. The brain mask is used to exclude non-brain regions from further analysis, improving computational efficiency and accuracy. However, the skull-stripped brain mask is not perfect and may require further refinement to ensure better segmentation.
3. patch2self.py : Implements a self-supervised denoising algorithm for diffusion MRI data, known as Patch2Self. After skull-stripping and brain masking, Patch2Self is applied to the DWI data to improve the signal quality. 
4. dti_analysis.py : Performs Diffusion Tensor Imaging (DTI) analysis, computing tensor-derived metrics such as Fractional Anisotropy (FA), Mean Diffusivity (MD), Axial Diffusivity (AD), and Radial Diffusivity (RD). These metrics are crucial for assessing white matter integrity.
    - Tensor Model Fitting: Uses a standard diffusion tensor model to fit the data and estimate FA, MD, AD, and RD.
5. pipeline.py: Runs tractography on the processed diffusion data, reconstructing white matter pathways. It utilizes probabilistic tracking methods to generate streamlines that represent white matter connections.
    - Seed Generation: Seeding points for tractography are created based on FA thresholds.
    - Stopping Criterion: The Generalized Fractional Anisotropy (GFA) metric from CsaOdfModel is used to determine when to stop tracking streamlines.
    - Direction Estimation: Constrained Spherical Deconvolution (CSD) is used to probabilistically estimate fiber directions, improving tracking in crossing-fiber regions.
    - Streamline Generation: Local probabilistic tracking is performed using the estimated fiber orientations and stopping criteria.

Additional Scripts:
1. dicom_to_bids.sh: It Cconverts MRI DICOM files into NIfTI format and organizes them into a BIDS-compliant structure.
    - A CSV file (ListPN_MRI.csv) containing MRI IDs and metadata.
    - Reads MRI IDs from the CSV file (ListPN_MRI.csv) and selects files where FullXP equals 1.0.
2. heuristic.py: It provides the rules for organizing and converting DICOM files into BIDS format.
3. mri_id_to_sub_id.: It maps MRI IDs to subject IDs
   - Reads from the CSV file SubIDs.csv
4. csamodel.py
   - Visualization: Generates and saves direction field and GFA images for quality assessment.
5. hmask_juelich.py: This script generates masks for the left and right hippocampus based on specific intensity values from the Juelich maxprob (thresholded) atlas in the MNI space. The created masks are saved as NIfTI files and can be used for further analysis or processing in neuroimaging studies.
