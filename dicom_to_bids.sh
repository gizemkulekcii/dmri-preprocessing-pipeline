#!/bin/bash

# Define paths for folders
PathFolder="/home/gizem/dzne/MRI_dicoms"
#PathRawFolder="/home/gizem/dzne/MRI_dicoms/dicoms/PostAssessment"
PathRawFolder="/home/gizem/dzne/MRI_dicoms/dicoms/PreAssessment"

# Initialize an array to store MRI IDs to process
declare -a MRI2Do_R
Counter_MRI=0 # Counter for the MRI2Do_R array

# Read data from CSV file
IFS=";"
while read Date MRI_ID Subject_ID FullXP; do
  # Remove spaces and carriage return from FullXP
  FullXP=$(echo "$FullXP" | tr -d ' \r')

  # Debugging: Print extracted values
  #echo "Read: Date=$Date, MRI_ID=$MRI_ID, SUBJECT_ID=$Subject_ID, FullXP=$FullXP

  # Check if FullXP value is 1.0
  if [ $FullXP = "1.0" ];then
    MRI2Do_R[$Counter_MRI]="$MRI_ID"
    ((Counter_MRI++))
  fi

done < "ListPN_MRI.csv"
#echo ${MRI2Do_R[@]}

# Initialize an array to store matching files
declare -a List_PN
Counter=0 # Counter for List_PN array

# Loop through all .tar files in the directory
for DataPN in "$PathRawFolder"/*.tar; do

    DataPN="${DataPN%/}"  # Remove trailing slashes if any
    result="${DataPN##*/}"  # Extract filename from the path

    # Extract the first two parts of the filename (assumed format)
    Name_PM=$(echo "$result" | cut -f1,2 -d'_')

    # Check extracted Name_PM
    # echo "Processing:$Name_PM"

    # Check if Name_PM exists in MRI2Do_R
    for item in "${MRI2Do_R[@]}"; do
      # Compare extracted values
      # echo "Comparing: '$item' vs '$Name_PM'"

      if [ "$item" == "$Name_PM" ]; then
            List_PN[$Counter]="$Name_PM"
            ((Counter++))

            # Extract the .tar file into the temporary directory
            tar -C "$PathFolder/dicoms/TempData" -xvf "$DataPN"

            # Set permissions to allow access
            chmod -R a+X "$PathFolder/dicoms/TempData/$Name_PM/"
            break  # Exit loop once match is found
        fi
    done
done

# Print the list of processed items
# printf '%s\n' "${List_PN[@]}"

# Define path for NIfTI conversion
PathforNiftii="DATAnifti/pre"
#echo $PathFolder/$PathforNiftii/

docker run --rm -v "$PathFolder":/PathFolder  nipy/heudiconv:latest -d /PathFolder/dicoms/TempData/{subject}/*/*/* -o /PathFolder/DATAnifti/pre/ -f convertall -s ${List_PN[0]} -c none --overwrite

# Copy the dicominfo.tsv file to the output folder
cp $PathFolder/$PathforNiftii/.heudiconv/${List_PN[0]}/info/dicominfo.tsv $PathFolder/$PathforNiftii

#Get the data in BIDS format
for q in "${MRI2Do_R[@]}";
do
  echo $q
  docker run --rm -it -v "$PathFolder":/PathFolder  nipy/heudiconv:latest -d /PathFolder/dicoms/TempData/{subject}/*/*/* -o /PathFolder/$PathforNiftii -f /PathFolder/DATAnifti/code/heuristic.py -s $q -c dcm2niix -b --overwrite --ses pre
  echo "Complete: " $q
done