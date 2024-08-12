# create a dataframe from the combined json and output to a csv
# %%
import pandas as pd
import json

'''
The json file is a list of dictionaries, the top level keys are the server names, 
the next key level is the catalog files, which contains a list of each dataset in the catalog.
Each dataset in a catalog is a dictionary with keys that should also be columns in the dataframe.
This script will create a dataframe from the json file and output to a csv file.
The csv file will have the following columns:
    server_name, catalog, dataset_name, type, server_location, tds_path, tds_id, parent_catalog, mount_path, writeable
'''

# read the json file using json.load
with open('output/combined.json', 'r') as f:
    data = json.load(f)
data

# %%
# build a datafram with all the columns
df = pd.DataFrame(columns=['server_name', 'catalog', 'dataset_name', 'type', 'server_location', 'tds_path', 'tds_id', 'parent_catalog', 'mount_path', 'writeable'])
df
# %%
# loop through the json data and append to the dataframe
rows = []
for server in data:
    # get the server name as the key at the toplevel
    server_name = list(server.keys())[0]
    # get each catalog for the server which are nested dictionaries. 
    # Iterate through the catalogs by getting the key and value.
    for catalog, datasets in server[server_name].items():
        for dataset in datasets:
            rows.append({
                'server_name': server_name, 
                'catalog': catalog, 
                'dataset_name': dataset['name'], 
                'type': dataset['type'], 
                'server_location': dataset['server_location'], 
                'tds_path': dataset['tds_path'], 
                'tds_id': dataset['tds_id'], 
                'parent_catalog': dataset['parent_catalog'], 
                'mount_path': dataset['mount_path'], 
                'writeable': dataset['writeable']
            })
        # print ('\n\nServer:\n',server_name,'\nCatalog:\n', catalog,'\nDataset:\n', dataset)
            # dict = 
            # {
                #  'server_name': server_name, 
                #  'catalog': catalog, 
                #  'dataset_name': dataset['name'], 
                #  'type': dataset['type'], 
                #  'server_location': dataset['server_location'], 
                #  'tds_path': dataset['tds_path'], 
                #  'tds_id': dataset['tds_id'], 
                #  'parent_catalog': dataset['parent_catalog'], 
                #  'mount_path': dataset['mount_path'], 
                #  'writeable': dataset['writeable']
            # }

# %%
# create a dataframe from the rows
df = pd.DataFrame(rows)
df
# %%
# output the dataframe to a csv file
df.to_csv('output/all_tds_datasets.csv', index=False)
# %%
