import os
import pandas as pd

def rename_files_recursively(folder_path, old_id, new_id):
    """ Recursively renames all files inside a folder, replacing old_id with new_id in filenames. """
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            if old_id in filename:  # Check if the filename contains the old ID
                old_file_path = os.path.join(dirpath, filename)
                new_filename = filename.replace(old_id, new_id)
                new_file_path = os.path.join(dirpath, new_filename)

                os.rename(old_file_path, new_file_path)
                print(f"Renamed file: {filename} → {new_filename}")


df = pd.read_csv("SubIDs.csv")
# Define the root directory containing subject folders
root_dir = 'BIDS/derivatives'  

mri_to_sub = dict(zip(df["MRI_ID"].astype(str), df["Subject_ID"].astype(str)))

for mri_id in os.listdir(root_dir):
    subject_dir = os.path.join(root_dir, mri_id)

    # Check if it's a directory and if the MRI_ID exists in the CSV
    if os.path.isdir(subject_dir) and mri_id in mri_to_sub:
        new_name = mri_to_sub[mri_id]  # Get the corresponding sub_id
        new_subject_dir = os.path.join(root_dir, new_name)  # New folder name

        # Rename all files inside the folder (including subfolders)
        rename_files_recursively(subject_dir, mri_id, new_name)

        # Rename the subject directory itself
        os.rename(subject_dir, new_subject_dir)
        print(f"Renamed folder: {mri_id} → {new_name}")
'''
import os

# Define the root directory where renaming should happen
root_dir = "post"  # Change this if needed

def rename_files_recursively(folder_path):
    """ Recursively renames all files and subfolders inside a folder, replacing 'pre' with 'post'. """
    for dirpath, dirnames, filenames in os.walk(folder_path, topdown=False):  
        # Rename files
        for filename in filenames:
            if "pre" in filename:
                old_file_path = os.path.join(dirpath, filename)
                new_filename = filename.replace("pre", "post")
                new_file_path = os.path.join(dirpath, new_filename)

                os.rename(old_file_path, new_file_path)
                print(f"Renamed file: {filename} → {new_filename}")

        # Rename subdirectories
        for dirname in dirnames:
            if "pre" in dirname:
                old_dir_path = os.path.join(dirpath, dirname)
                new_dirname = dirname.replace("pre", "post")
                new_dir_path = os.path.join(dirpath, new_dirname)

                os.rename(old_dir_path, new_dir_path)
                print(f"Renamed folder: {dirname} → {new_dirname}")

# Apply renaming inside the "pre" folder
rename_files_recursively(root_dir)

# Rename the root folder itself if it is named "pre"
if os.path.exists(root_dir) and "pre" in root_dir:
    new_root_dir = root_dir.replace("pre", "post")
    os.rename(root_dir, new_root_dir)
    print(f"Renamed root folder: {root_dir} → {new_root_dir}")
'''