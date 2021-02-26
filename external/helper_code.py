#!/usr/bin/env python

# These are helper variables and functions that you can use with your code.
# Do not edit this script.

import numpy as np
import os
from scipy.io import loadmat

# Define 12, 6, and 2 lead ECG sets.
twelve_leads = ('I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6')
six_leads = ('I', 'II', 'III', 'aVR', 'aVL', 'aVF')
two_leads = ('II', 'V5')

# Check if a variable is an integer or represents an integer.
def is_integer(x):
    try:
        if int(x)==float(x):
            return True
        else:
            return False
    except (ValueError, TypeError):
        return False

# Find header and recording files.
def find_challenge_files(data_directory):
    header_files = list()
    recording_files = list()
    for f in os.listdir(data_directory):
        root, extension = os.path.splitext(f)
        if not root.startswith('.') and extension=='.hea':
            header_file = os.path.join(data_directory, root + '.hea')
            recording_file = os.path.join(data_directory, root + '.mat')
            if os.path.isfile(header_file) and os.path.isfile(recording_file):
                header_files.append(header_file)
                recording_files.append(recording_file)
    return header_files, recording_files

# Load header file as a string.
def load_header(header_file):
    with open(header_file, 'r') as f:
        header = f.read()
    return header

# Load recording file as an array.
def load_recording(recording_file, header=None, leads=None, key='val'):
    x = loadmat(recording_file)[key]
    recording = np.asarray(x, dtype=np.float32)
    return recording

# Get leads from header.
def get_leads(header):
    leads = list()
    for i, l in enumerate(header.split('\n')):
        entries = l.split(' ')
        if i==0:
            num_leads = int(entries[1])
        elif i<=num_leads:
            leads.append(entries[-1])
        else:
            break
    return leads

# Get age from header.
def get_age(header):
    age = None
    for l in header.split('\n'):
        if l.startswith('#Age'):
            try:
                age = float(l.split(': ')[1].strip())
            except:
                age = float('nan')
    return age

# Get age from header.
def get_sex(header):
    sex = None
    for l in header.split('\n'):
        if l.startswith('#Sex'):
            try:
                sex = l.split(': ')[1].strip()
            except:
                pass
    return sex

# Get frequency from header.
def get_frequency(header):
    frequency = None
    for i, l in enumerate(header.split('\n')):
        if i==0:
            try:
                frequency = float(l.split(' ')[2])
            except:
                pass
        else:
            break
    return frequency

# Get amplitudes from header.
def get_amplitudes(header, leads):
    amplitudes = np.zeros(len(leads), dtype=np.float32)
    for i, l in enumerate(header.split('\n')):
        entries = l.split(' ')
        if i==0:
            num_leads = int(entries[1])
        elif i<=num_leads:
            current_lead = entries[-1]
            if current_lead in leads:
                j = leads.index(current_lead)
                try:
                    amplitudes[j] = float(entries[2].split('/')[0])
                except:
                    pass
        else:
            break
    return amplitudes

# Get baselines from header.
def get_baselines(header, leads):
    baselines = np.zeros(len(leads), dtype=np.float32)
    for i, l in enumerate(header.split('\n')):
        entries = l.split(' ')
        if i==0:
            num_leads = int(entries[1])
        elif i<=num_leads:
            current_lead = entries[-1]
            if current_lead in leads:
                j = leads.index(current_lead)
                try:
                    baselines[j] = float(entries[4].split('/')[0])
                except:
                    pass
        else:
            break
    return baselines

# Get labels from header.
def get_labels(header):
    labels = list()
    for l in header.split('\n'):
        if l.startswith('#Dx'):
            entries = l.split(': ')[1].split(',')
            for entry in entries:
                labels.append(entry.strip())
    return labels

# Save outputs from model.
def save_outputs(output_file, classes, labels, probabilities):
    # Extract the recording identifier from the filename.
    head, tail = os.path.split(output_file)
    root, extension = os.path.splitext(tail)
    recording_identifier = root

    # Format the model outputs.
    recording_string = '#{}'.format(recording_identifier)
    class_string = ','.join(str(c) for c in classes)
    label_string = ','.join(str(l) for l in labels)
    probabilities_string = ','.join(str(p) for p in probabilities)
    output_string = recording_string + '\n' + class_string + '\n' + label_string + '\n' + probabilities_string + '\n'

    # Save the model outputs.
    with open(output_file, 'w') as f:
        f.write(output_string)


def get_classes(files_without_ext):
    classes = set()
    for filename in files_without_ext:
        with open(filename+'.hea', 'r') as f:
            for l in f:
                if l.startswith('#Dx'):
                    tmp = l.split(':')[1].split(',')
                    for c in tmp:
                        classes.add(c.strip())
    return dict(zip(sorted(classes), range(len(classes))))

def encode_header_labels(header, classes):
    labels_act = np.zeros(len(classes))
    for l in header.split('\n'):
        if l.startswith('#Dx'):
            tmp = l.split(':')[1].split(',')
            for c in tmp:
                class_index = classes[c.strip()]
                labels_act[class_index] = 1
    return labels_act

def save_challenge_predictions(output_directory, filenames, classes, scores, labels):
    for i in range(0, len(filenames)):
        filename = filenames[i]
        sc = scores[i]
        ls = labels[i]
        recording = os.path.splitext(filename)[0]
        new_file = filename.replace('.mat','.csv')
        output_file = os.path.join(output_directory,new_file)

        # Include the filename as the recording number
        recording_string = '#{}'.format(recording)
        class_string = ','.join(classes)
        label_string = ','.join(str(i) for i in ls)
        score_string = ','.join(str(i) for i in sc)

        with open(output_file, 'w') as f:
            f.write(recording_string + '\n' + class_string + '\n' + label_string + '\n' + score_string + '\n')