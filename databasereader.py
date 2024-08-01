import os
import csv
import sqlite3
import pickle
import pickle as pkl
import json
import numpy as np
import pandas as pd
from PIL import Image
from datetime import datetime
import pytz
from scipy import ndimage as ndi

# Define paths to database and specify the name of index contained within;
DATASET_PATH = '/Users/antonia/Desktop/ADE20K_2021_17_01'
entry_path = '/Users/antonia/Desktop'
index_file = 'index.pkl'
#use n_images_read to adjust how many images are read at one time
n_images_read = 5
last_printed_percentage = 0

def main ():
    
    global last_printed_percentage
    # Load the pickle file
    index_path = os.path.join(entry_path, 'ADE20K_2021_17_01/index.pkl')
    with open(index_path, 'rb') as f:
        index = pickle.load(f)
        # Check if the index is not empty
        if index:
            print("\nindex.pkl successfully loaded!")
        else:
            print("Error: index.pkl is empty or could not be loaded.")
            # Access the filename and folder lists
    filenames = index['filename']
    folders = index['folder']

    # Prepare data for the first n_images_read number of images
    data = []
    for i in range(n_images_read):
        image_name = filenames[i]
        folder_name = folders[i]
        #nr is the position of the image within the created list
        nr = [i]
        full_image_path_on_my_mac = os.path.join(entry_path, folder_name, image_name)
        #to be used if needed
        full_image_path_for_another_user = os.path.join(folder_name, image_name)
        json_file_path = os.path.splitext(full_image_path_on_my_mac)[0] + '.json'
        
        # Check if the file exists
        if os.path.exists(full_image_path_on_my_mac):
            #open json file containing information about given image
            with open(json_file_path, 'r') as json_file:
                json_data = json.load(json_file)
                #find name data of every object in photo in the json file                    
                # Check if 'scene' key exists and extract its values
                if 'scene' in json_data['annotation']:
                    in_or_out = json_data['annotation']['scene'][0]
                    image_categories = json_data['annotation']['scene'][1]
                    scene = json_data['annotation']['scene'][2]
                else:
                    in_or_out = "No scene data"
                    image_categories = "No scene data"
                    scene = "No scene data"
                
           # Get the annotation section
                annotations = json_data['annotation']
                # Initialize a dictionary to keep track of the object counts
                object_counts = {}
                # Initialize a list to store the unique object names
                unique_objects = []
                # Initialize a list to store the mask area sizes and another to store center of mass coordinates
                mask_area_sizes = []
                center_of_mass_coords = []
                # Initialize a list to store object types
                obj_names_without_instances = []

                for obj in json_data['annotation']['object']:
                    # Get the object name
                    obj_name = obj['raw_name']
                    
                    # If the name is already in the dictionary, increment the count
                    if obj_name in object_counts:
                        object_counts[obj_name] += 1
                    else:
                        object_counts[obj_name] = 1
                    
                    if obj_name not in obj_names_without_instances:
                        obj_names_without_instances.append(obj_name)
                    objectTypes_str = ', '.join(obj_names_without_instances)
                    

                    # Create a unique name for the object
                    obj_name_adj4duplicates = f"{obj_name}{object_counts[obj_name]}"
                    unique_objects.append(obj_name_adj4duplicates)                 
                    object_instances_str = ', '.join(unique_objects)

                    # Get the instance mask path
                    instance_mask_path = obj['instance_mask']
                    #Use this path if needed, to locate a specific 
                    full_mask_path = os.path.join(entry_path, folder_name, instance_mask_path)
                    # Calculate the white area in the mask
                    white_area_size_for1mask, center_of_mass_for1mask = calculate_white_area_and_center_of_mass(full_mask_path)
                    mask_area_sizes.append(white_area_size_for1mask)
                    mask_sizes_str = ', '.join(map(str, mask_area_sizes))
                    center_of_mass_coords.append(center_of_mass_for1mask)
                    center_of_mass_str = '; '.join([f'({cy}, {cx})' for cy, cx in center_of_mass_coords])
            
            with Image.open(full_image_path_on_my_mac) as image:
                #Image.size gives a 2-tuple and the width, height can be obtained
                width, height = image.size
                #calculate aspect ratio and number of pixels
                aspect_ratio = round(width/height, 4)
                pixel_no = width*height

            #PROGRESS COUNTER to keep track of progress in the program
            n_images_read_so_far = (i+1)
            current_time = datetime.now(pytz.timezone('Europe/Warsaw'))
            # Calculate the percentage completed
            percentage_completed = (n_images_read_so_far) / n_images_read * 100
            if i == (n_images_read-1):
                print(f"{current_time}  Program has completed work at {n_images_read_so_far} images.")
            # print progress message at each 10% completed
            # Calculate the percentage completed
            percentage_completed = (i+1) * 100 // n_images_read
            # Print progress for each 10% completion
            if percentage_completed >= last_printed_percentage + 10:
                print(f"{current_time}  Progress: {percentage_completed}% completed")
                last_printed_percentage = percentage_completed

            

        else:
            print(f"Image {full_image_path_on_my_mac} does not exist.")
            
        #this appends data to concrete places in the CSV spreadsheet
        data.append({
            'nr': nr,
            'filename': image_name, 
            'folder': folder_name, 
            'isInside': in_or_out,
            "category": image_categories,
            'scene': scene,
            'resolution': str(width) + "x" + str(height),
            'pixelNr': pixel_no,
            'aspectRatio': aspect_ratio,
            'objectTypes': objectTypes_str,
            'objectInstances': object_instances_str,
            'maskSizeOfEachObjectInstance': mask_sizes_str,
            'centerOfMassForEachMaskCyCx': center_of_mass_str
        })
            
    # Convert to DataFrame and save to CSV
    df = pd.DataFrame(data)
    output_csv_path = os.path.join(DATASET_PATH,'image_info_table.csv')
    df.to_csv(output_csv_path, index=False)
    print(f"\nCSV file saved at {output_csv_path}\n")

def calculate_white_area_and_center_of_mass(image_path):
    # Open the image file
    with Image.open(image_path) as img:
        # Convert the image to grayscale
        gray_image = img.convert("L")
        # Convert grayscale image to numpy array
        img_array = np.array(gray_image)
        # Create a binary image where white is 1 and everything else is 0
        binary_img = (img_array == 255).astype(int)
        # Calculate the white area by summing the binary image
        white_area = binary_img.sum()
        # Calculate the center of mass of the white area
        if white_area > 0:
            cy, cx = ndi.center_of_mass(binary_img)
            cy = round(cy, 2)
            cx = round(cx, 2)
        else:
            cy, cx = None, None
        return white_area, (cy, cx)
    

def print_datatype_of_index ():
    # Optionally, print the type of the loaded data
    print(f"Data type of loaded index: {type(index)}")

def print_total_number_of_keys ():
    # Get the total number of keys
    num_keys = len(index)
    print(f"Total number of keys: {num_keys}")

def print_datatype_for_each_key ():
    # Get the type of the value associated with the first key
    key_counter = 0
    while key_counter<15:
        read_key = list(index.keys())[key_counter]
        value_type = type(index[read_key])
        print(f"Type of value associated with the {key_counter} key: {value_type}")
        key_counter+=1

main()
