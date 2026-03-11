#!/bin/bash

OUTPUT_DIR_TOPUP="derivatives/topup_output"
OUTPUT_DIR_EDDY="derivatives/eddy_output"
EDDY_QC="derivatives/eddy_qc"
EDDY_SQUAD_QC="derivatives/eddy_squad_qc"

# Ensure output directories exist
mkdir -p "$OUTPUT_DIR_TOPUP"
mkdir -p "$OUTPUT_DIR_EDDY"
mkdir -p "$EDDY_QC"
mkdir -p "$EDDY_SQUAD_QC"

echo "Starting processing for all subjects..."

for subject in sub*;do
   for ses_dir in "${subject}"/ses-*;do
        session_id=$(basename "$ses_dir") 
        echo "Processing: ${subject} in ${session_id}"
        
        DWI_DIR=${subject}/${session_id}/dwi/

        # Ensure subject-specific output directories exist
        mkdir -p "$OUTPUT_DIR_TOPUP/${subject}/${session_id}"
        mkdir -p "$OUTPUT_DIR_EDDY/${subject}/${session_id}"

        # Define file paths
        b0_PA_file="${DWI_DIR}${subject}_${session_id}_acq-b0_dir-PA_dwi.nii.gz"
        b1000_AP_file="${DWI_DIR}${subject}_${session_id}_acq-b1000_dir-AP_dwi.nii.gz"

        b0_AP_file="${DWI_DIR}${subject}_${session_id}_acq-b0_dir-AP_dwi.nii.gz"
        b0_AP_PA_file="${OUTPUT_DIR_TOPUP}/${subject}/${session_id}/${subject}_${session_id}_acq-b0_dir-AP-PA_dwi.nii.gz"
        acqparams_file="acqparams.txt"
        index_file="${OUTPUT_DIR_EDDY}/${subject}/${session_id}/index.txt"

        # Check if b0 and b1000 images exist
        if [[ -f "$b0_PA_file" && -f "$b1000_AP_file" ]]; then
            #echo "All required files exist. Proceeding with preprocessing for ${subject} in ${session_id}"
            
            # Extract first volume from b1000_AP_file to create b0_AP_file
            fslroi "$b1000_AP_file" "$b0_AP_file" 0 1
            
            # Merge b0_AP and b0_PA to create AP-PA file
            fslmerge -t "$b0_AP_PA_file" "$b0_AP_file" "$b0_PA_file"
            
            # Check if merged b0_AP_PA file exists before proceeding
            if [[ -f "$b0_AP_PA_file" ]]; then
                # Run TOPUP
                topup --imain="$b0_AP_PA_file" \
                    --acqp="$acqparams_file" \
                    --config=b02b0.cnf \
                    --out="$OUTPUT_DIR_TOPUP/${subject}/${session_id}/${subject}_${session_id}_topup_AP_PA_b0" \
                    --iout="$OUTPUT_DIR_TOPUP/${subject}/${session_id}/${subject}_${session_id}_topup_AP_PA_b0_iout" \
                    --fout="$OUTPUT_DIR_TOPUP/${subject}/${session_id}/${subject}_${session_id}_topup_AP_PA_b0_fout" 

                echo "TOPUP completed for $subject in $ses_dir"
            
                # Compute mean of topup-corrected b0 images
                fslmaths "$OUTPUT_DIR_TOPUP/${subject}/${session_id}/${subject}_${session_id}_topup_AP_PA_b0_iout" -Tmean "$OUTPUT_DIR_EDDY/${subject}/${session_id}/${subject}_${session_id}_hifi_b0"
                
                # Brain extraction
                bet "$OUTPUT_DIR_EDDY/${subject}/${session_id}/${subject}_${session_id}_hifi_b0" "$OUTPUT_DIR_EDDY/${subject}/${session_id}/${subject}_${session_id}_hifi_b0_brain" -m -f 0.2

                # Create index file for eddy
                num_vols=$(fslval "$b1000_AP_file" dim4)
                echo "Number of volumes in $b1000_AP_file: $num_vols"

                indx=""
                for ((i=1; i<=$num_vols; i+=1)); do indx="$indx 1"; done
                echo $indx > "$index_file"

                # Run eddy
                eddy --imain="$b1000_AP_file" \
                    --mask="$OUTPUT_DIR_EDDY/${subject}/${session_id}/${subject}_${session_id}_hifi_b0_brain_mask.nii.gz" \
                    --acqp="$acqparams_file" \
                    --index="$index_file" \
                    --bvecs="$DWI_DIR/${subject}_${session_id}_acq-b1000_dir-AP_dwi.bvec" \
                    --bvals="$DWI_DIR/${subject}_${session_id}_acq-b1000_dir-AP_dwi.bval" \
                    --fwhm=0 \
                    --topup="$OUTPUT_DIR_TOPUP/${subject}/${session_id}/${subject}_${session_id}_topup_AP_PA_b0" \
                    --flm=quadratic \
                    --out="$OUTPUT_DIR_EDDY/${subject}/${session_id}/${subject}_${session_id}_eddy_corrected" \
                    --data_is_shelled
                echo " EDDY correction done for $subject in $session_id"

                # Run Eddy QC
                eddy_quad "$OUTPUT_DIR_EDDY/${subject}/${session_id}/${subject}_${session_id}_eddy_corrected" \
                -idx "$index_file" \
                -par "$acqparams_file" \
                -m "$OUTPUT_DIR_EDDY/${subject}/${session_id}/${subject}_${session_id}_hifi_b0_brain_mask.nii.gz" \
                -b "$DWI_DIR${subject}_${session_id}_acq-b1000_dir-AP_dwi.bval" \
                -g "$DWI_DIR${subject}_${session_id}_acq-b1000_dir-AP_dwi.bvec" \
                -o "$EDDY_QC/${subject}/${session_id}"

                echo "Eddy QC completed for $subject in $session_id"

            else
                echo "Error: Merged AP_PA_b0 file not found for $subject in $session_id"
            fi
        else
            echo "Error: Required DWI files missing for $subject in $session_id"
        fi
   done
done
echo "All subjects processed successfully."

'''
# Run SQUAD (Aggregated QC across all subjects).
if [ "$(ls -A "$EDDY_QC")" ]; then
    eddy_squad "$EDDY_QC" -o "$EDDY_SQUAD_QC"
    echo "SQUAD QC completed, results stored in $EDDY_SQUAD_QC"
else
    echo "No valid QC outputs found, skipping SQUAD."
fi
'''