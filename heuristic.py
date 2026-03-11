#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes
def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where
    allowed template fields - follow python string module:
    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """
    t1 = create_key('sub-{subject}/ses-post/anat/sub-{subject}_ses-post_T1w')
    t1_ND = create_key('sub-{subject}/ses-post/anat/sub-{subject}_ses-post_task-ND_T1w')
    t2_ear = create_key('sub-{subject}/ses-post/anat/sub-{subject}_ses-post_task-ear_T2w') #Series 13
    t2_ear_norm=create_key('sub-{subject}/ses-post/anat/sub-{subject}_ses-post_task-ear_norm_T2w') #Series 14
    t2=create_key('sub-{subject}/ses-post/anat/sub-{subject}_ses-post_T2w')
    dwi_b1000= create_key('sub-{subject}/ses-post/dwi/sub-{subject}_ses-post_acq-b1000_dir-AP_dwi')
    dwi_b1000_tracew= create_key('sub-{subject}/ses-post/dwi/sub-{subject}_ses-post_acq-b1000TRACEW_dir-AP_dwi')
    dwi_b0 = create_key('sub-{subject}/ses-post/dwi/sub-{subject}_ses-post_acq-b0_dir-PA_dwi')
    info = {t1:[], t1_ND:[], t2:[], t2_ear:[], t2_ear_norm:[], dwi_b1000:[], dwi_b1000_tracew:[], dwi_b0:[]}
    
    for idx, s in enumerate(seqinfo):
        if (s.dim1 == 256) and (s.dim2 == 256) and ('MPRAGE' in s.dcm_dir_name) and not ('PAT2_ND' in s.dcm_dir_name):
            info[t1].append(s.series_id)
        if (s.dim1 == 256) and (s.dim2 == 256) and ('PAT2_ND' in s.dcm_dir_name):
            info[t1_ND].append(s.series_id)
        if (s.dim3 == 64) and ('tse' in s.protocol_name):
            info[t2].append(s.series_id)
        if (s.dim3 == 56) and ('t2_space' in s.protocol_name) and ('series_13' in s.dcm_dir_name):
            info[t2_ear].append(s.series_id)
        if (s.dim3 == 56) and ('t2_space' in s.protocol_name) and ('series_14' in s.dcm_dir_name):
            info[t2_ear_norm].append(s.series_id)
        if (s.dim3 == 80) and ('DTI' in s.protocol_name) and ('b100' in s.protocol_name):
            info[dwi_b1000].append(s.series_id)
        if (s.dim3 == 320) and ('DTI' in s.protocol_name) and ('b100' in s.protocol_name):
            info[dwi_b1000_tracew].append(s.series_id)
        if (s.dim3 == 80) and ('DTI' in s.protocol_name) and ('b0' in s.protocol_name):
            info[dwi_b0].append(s.series_id)

    return info

