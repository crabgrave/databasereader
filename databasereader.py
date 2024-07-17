import os
import csv
import sqlite3
import pickle
import json




# Load the pickle file
with open('/Users/antonia/Desktop/ADE20K_2021_17_01/index.pkl', 'rb') as f:
    index = pickle.load(f)

# Check if the index is not empty
if index:
    print("index.pkl successfully loaded!")
else:
    print("Error: index.pkl is empty or could not be loaded.")

# Optionally, print the type of the loaded data
print(f"Data type of loaded index: {type(index)}")

# Get the total number of keys
num_keys = len(index)
print(f"Total number of keys: {num_keys}")


# Get the type of the value associated with the first key
key_counter = 0
while key_counter<15:
    read_key = list(index.keys())[key_counter]
    value_type = type(index[read_key])
    print(f"Type of value associated with the {key_counter} key: {value_type}")
    key_counter+=1