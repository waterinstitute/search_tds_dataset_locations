# for every json in the output directory, 
# that isnt the missing_datasets.json or the web_catalog_refs.json, 
# combine to a single json.
import json
import os
from glob import glob

def merge_jsons(file_paths, output_file):
    merged_data = []
    for path in file_paths:
        with open(path, 'r') as f:
            data = json.load(f)
            merged_data.append(data)
    with open(output_file, 'w') as f:
        json.dump(merged_data, f, indent=4)

# if the combined.json file already exists, delete it
if os.path.exists('output/combined.json'):
    os.remove('output/combined.json')

# create a list of all the json files in the output directory
file_paths = []
for json_file in glob('output/*.json'):
    if json_file == 'output/missing_datasets.json' \
    or json_file == 'output/missing_catalog_refs.json' \
    or json_file == 'output/web_catalog_refs.json' \
    or json_file == 'output/combined.json':
        continue
    else:
        file_paths.append(json_file)

merge_jsons(file_paths, 'output/combined.json')


