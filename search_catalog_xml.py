import os
import subprocess
import lxml.etree as ET
from pathlib import Path
import json

# function to get all catalogRefs in the catalog.xml file.
def getCatalogRefs(catalog_xml, catalog_ref, catalog_path):
    catalog_refs = [tag.get('{http://www.w3.org/1999/xlink}href') for tag in catalog_xml.iter() if tag.tag.endswith('catalogRef')]
    # add the catalog path to the catalog references
    catalog_refs = [catalog_path / ref for ref in catalog_refs]
    # if the catalog reference contains a directory of /../, remove the /../ and the previous directory from the path.
    catalog_refs = [Path(ref).resolve() for ref in catalog_refs]
    
    return catalog_refs

# refactor the function getCatalogRefs to output a dictionary with the catalog reference and the catalog path.
def getCatalogRefs(catalog_xml, catalog_ref, catalog_path):
    # print (f'\nFinding catalog references in: {catalog_ref}')
    catalog_refs = [tag.get('{http://www.w3.org/1999/xlink}href') for tag in catalog_xml.iter() if str(tag.tag).endswith('catalogRef')]
    # add the catalog path to the catalog references
    catalog_refs = [catalog_path / ref for ref in catalog_refs]
    # if the catalog reference contains a directory of /../, remove the /../ and the previous directory from the path.
    catalog_refs = [Path(ref).resolve() for ref in catalog_refs]
    # create a dictionary with the catalog reference and the catalog path.
    catalog_refs_dict = [{"parent": catalog_ref, "catalog": ref} for ref in catalog_refs]

    return catalog_refs, catalog_refs_dict

def updateCatalogRefs(catalog_refs, catalog_refs_dict, web_catalog_refs_dict):
    catalog_refs_sublist = []
    catalog_refs_sublist_dict = []
    hostname = subprocess.check_output(['hostname']).decode('utf-8').strip()

    for catalog_ref in catalog_refs:
        # remove the thredds_home_dir from the catalog_ref
        catalog_ref_rel_path = Path(catalog_ref).relative_to(thredds_home_dir)
        # remove the catalog.xml file name from the relative path
        catalog_ref_rel_path = catalog_ref_rel_path.parent
        # join the thredds_home_dir with the relative path
        catalog_path = thredds_home_dir / catalog_ref_rel_path
        # read the catalog file
        catalog_ref_str = str(catalog_ref)
        # if catalog_ref_str contains 'http://' or 'https://', do not parse, and add to a web reference list.
        if 'http:/' in catalog_ref_str or 'https:/' in catalog_ref_str:
            # split the catalog_ref_str by starting with 'http://' or 'https://'
            catalog_parent = catalog_ref_str.split('http:/')[0].split('https:/')[0]
            # remove the thredds home dir
            catalog_parent = catalog_parent.split(str(thredds_home_dir))[-1]
            catalog_ref_str = catalog_ref_str.split('http:/')[-1].split('https:/')[-1]
            web_catalog_refs_dict[hostname].append({
                "parent": catalog_parent,
                "catalog": catalog_ref_str
            })

            # don't parse the web catalog reference and go to the next catalog reference.
            continue
        catalog_ref_xml = ET.parse(catalog_ref_str)
        sublist, sublist_dict = getCatalogRefs(catalog_ref_xml, catalog_ref, catalog_path)
        catalog_refs_sublist += sublist
        catalog_refs_sublist_dict += sublist_dict

    return catalog_refs_sublist, catalog_refs_sublist_dict, web_catalog_refs_dict

def is_on_mount(path):
  while True:
    if path == os.path.dirname(path):
      # we've hit the root dir
      return False
    elif os.path.ismount(path):
      return True
    path = os.path.dirname(path)

# get hostname
hostname = subprocess.check_output(['hostname']).decode('utf-8').strip()

# define the missing datasets json file to append any missing datasets to.
missing_datasets = 'output/missing_datasets.json'
# open the missing datasets json file and if it does not exist, create it.
try:
    with open(missing_datasets, 'r') as f:
        missing_datasets_dict = json.load(f)
except FileNotFoundError:
    missing_datasets_dict = {}
    with open(missing_datasets, 'w') as f:
        json.dump(missing_datasets_dict, f, indent=4)
# Create a key in the missing_datasets_dict for the hostname
missing_datasets_dict[hostname] = []

# define web catalog references json file, and if it does not exist, create it..
web_catalog_refs = 'output/web_catalog_refs.json'
try:
    with open(web_catalog_refs, 'r') as f:
        web_catalog_refs_dict = json.load(f)
except FileNotFoundError:
    web_catalog_refs_dict = {}
    with open(web_catalog_refs, 'w') as f:
        json.dump(web_catalog_refs_dict, f, indent=4)
# Create a key in the web_catalog_refs_dict for the hostname
web_catalog_refs_dict[hostname] = []

# read /var/lib/tomcat/content/thredds/catalog.xml and parse it for additional catalog references.
# read the catalog.xml file
thredds_home_dir = Path('/var/lib/tomcat/content/thredds/')
# join the thredds_home_dir with the catalog.xml file
catalog_ref = thredds_home_dir / 'catalog.xml'
# catalog_ref = thredds_home_dir + 'catalog.xml'
catalog_xml = ET.parse(str(catalog_ref))

# additional catalog references are stored in the <catalogRef> tag and have a 'xlink:href' attribute for the location of the catalog.
# find all <catalogRef> tags in the catalog.xml file
catalog_refs, catalog_refs_dict = getCatalogRefs(catalog_xml, catalog_ref, thredds_home_dir)


# remove duplicates from the catalog_refs and catalog_refs_dict
catalog_refs = list(set(catalog_refs))
catalog_refs_dict = [i for n, i in enumerate(catalog_refs_dict) if i not in catalog_refs_dict[n + 1:]]

# print (f'Catalogs before updating with sublists: {len(catalog_refs)}\n')
# print (f'Catalog dicts before updating with sublists: {len(catalog_refs_dict)}\n')

# for each catalog reference, read the catalog file, and parse it for additional catalog references. add these to the list of catalog references.
# run updateCatalogRefs until there are no additional sub catalog references.
n = 0
catalog_refs_sublist, catalog_refs_sublist_dict, web_catalog_refs_dict = updateCatalogRefs(catalog_refs, catalog_refs_dict, web_catalog_refs_dict)
while len(catalog_refs_sublist) > 0:
    # Update catalog reference list with sublist n.
    catalog_refs += catalog_refs_sublist
    catalog_refs_dict += catalog_refs_sublist_dict
    # Update web catalog reference list
    n+=1
    # print(f'\nFound nested catalogs \n Parsing nested catalog {n}. \n')    
    # Get new sublist
    catalog_refs_sublist, sublist_dict, web_catalog_refs_dict = updateCatalogRefs(catalog_refs_sublist, catalog_refs_dict, web_catalog_refs_dict)

# remove duplicates from the catalog_refs and catalog_refs_dict
catalog_refs = list(set(catalog_refs))
catalog_refs_dict = [i for n, i in enumerate(catalog_refs_dict) if i not in catalog_refs_dict[n + 1:]]

# add the catalog.xml file to the catalog_refs list
catalog_refs.append('/var/lib/tomcat/content/thredds/catalog.xml')
catalog_refs_dict.append({"parent": None, "catalog": '/var/lib/tomcat/content/thredds/catalog.xml'})

# Update the catalog references to remove the thredds_home_dir from the catalog dictionary.
for ref in catalog_refs_dict:
    ref['catalog'] = str(Path(ref['catalog']).relative_to(thredds_home_dir))
    if ref['parent'] is not None:
        ref['parent'] = str(Path(ref['parent']).relative_to(thredds_home_dir))

# Sort the dictionary
catalog_refs_dict.sort(key=lambda x: x['catalog'])
# print (f'Catalog dicts: {catalog_refs_dict}\n')

# create a dictionary to store the dataset locations for each catalog reference.
catalog_datasets_dict = {}
catalog_datasets_dict[hostname] = {}
# for each catalog key in each item in the catalog_refs_dict, read the catalog file, parse it to find the dataset locations, 
# and finally add the dataset location and other attrs to the dictionary.
for catalog_ref in catalog_refs_dict:
    # print('\n', catalog_ref)
    # create a string from catalog ref that is just the end name of the catalog reference and drop the extension
    catalog_ref_key = Path(catalog_ref['catalog']).stem
    catalog_ref_str = catalog_ref['catalog']
    # get the parent catalog reference
    catalog_ref_parent = str(catalog_ref['parent'])
    # add a key to the dictionary for the catalog reference add an empty list as the value to append each found dataset location.
    
    catalog_datasets_dict[hostname][catalog_ref_str] = []
    
    catalog_ref = thredds_home_dir / catalog_ref['catalog']
    catalog_xml = ET.parse(str(catalog_ref))
    # dataset locations are stored in the <datasetScan> and <datasetRoot> tags and have a 'location' attribute for the location of the dataset.
    for tag in catalog_xml.iter():
        if str(tag.tag).endswith('datasetScan') or str(tag.tag).endswith('datasetRoot'):
            # print ('\ndataset tag found\n')
            # use the server location attribute to get the mount path.
            is_mounted = is_on_mount(tag.get('location'))
            writeable = os.access(tag.get('location'), os.W_OK)
            if os.path.exists(tag.get('location')):
                location = tag.get('location')
                if is_mounted:
                    # check if the locatiion exists
                        # run a subprocess to use findmnt -n 0o SOURCE --target path
                        # to get the source of the mount.
                        mnt_path = subprocess.check_output(['findmnt', '-n', '-o', 'SOURCE', '--target', tag.get('location')])        
                        mnt_path = mnt_path.decode('utf-8').strip()
                else:
                    # the path exists but is not mounted.
                    mnt_path = None
            else:
                # the path does not exist. set the mount path to None and add the location to the missing datasets dictionary.
                mnt_path = None
                location = f"Path does not exist on server: {tag.get('location')}"
                missing_datasets_dict[hostname].append({
                    "name": tag.get('name'),
                    "catalog": str(catalog_ref),
                    "type": tag.tag.split('}')[-1],
                    "missing_server_location": tag.get('location'),
                    "tds_path": tag.get('path'),
                    "tds_id": tag.get('ID'),
                    "parent_catalog": catalog_ref_parent,
                    "mount_path": mnt_path,
                    "writeable": writeable
                })


            # append the location attribute to the list of dataset locations for the catalog reference.
            catalog_datasets_dict[hostname][catalog_ref_str].append({
                "name": tag.get('name'),
                "catalog": str(catalog_ref),
                "type": tag.tag.split('}')[-1],
                "server_location": location,
                "tds_path": tag.get('path'),
                "tds_id": tag.get('ID'),
                "parent_catalog": catalog_ref_parent,
                "mount_path": mnt_path,
                "writeable": writeable
            })

        # search for featureCollections
        if str(tag.tag).endswith('featureCollection'):
            # find any collection tags within the featureCollection tag
            collection_paths = []
            spec_parents = []
            for collection in tag.iter():
                if str(collection.tag).endswith('collection'):
                    spec = collection.get('spec')
                    spec_parent = collection.get('spec')
                    # while spec path contains *, get parent directory
                    while '*' in spec_parent:
                        spec_parent = os.path.dirname(spec_parent)        
                    collection_paths.append(spec)
                    spec_parents.append(spec_parent)
            
            # use the server location attribute to get the mount path.
            is_mounted = is_on_mount(spec_parents[0])
            writeable = os.access(spec_parents[0], os.W_OK)
            if os.path.exists(spec_parents[0]):
                location = spec_parents[0]
                if is_mounted:
                    # check if the locatiion exists
                        # run a subprocess to use findmnt -n 0o SOURCE --target path
                        # to get the source of the mount.
                        mnt_path = subprocess.check_output(['findmnt', '-n', '-o', 'SOURCE', '--target', spec_parents[0]])        
                        mnt_path = mnt_path.decode('utf-8').strip()
                else:
                    # the path exists but is not mounted.
                    mnt_path = None
            else:
                # the path does not exist. set the mount path to None and add the location to the missing datasets dictionary.
                mnt_path = None
                location = f"Path does not exist on server: {spec_parents[0]}"
                missing_datasets_dict[hostname].append({
                    "name": tag.get('name'),
                    "catalog": str(catalog_ref),
                    "type": tag.tag.split('}')[-1],
                    "missing_server_location": location,
                    "tds_path": tag.get('path'),
                    "tds_id": tag.get('ID'),
                    "parent_catalog": catalog_ref_parent,
                    "mount_path": mnt_path,
                    "writeable": writeable,
                    "collection_paths": collection_paths

                })

            # add the collection to the catalog_datasets_dict
            catalog_datasets_dict[hostname][catalog_ref_str].append({
                "name": tag.get('name'),
                "catalog": str(catalog_ref),
                "type": tag.tag.split('}')[-1],
                "server_location": location,
                "tds_path": tag.get('path'),
                "tds_id": tag.get('ID'),
                "parent_catalog": catalog_ref_parent,
                "mount_path": None,
                "writeable": None,
                "collection_paths": collection_paths
            })
        

# if a key in the catalog_datasets_dict has no dataset locations, add a nested dictionary with the catalog, parent and the rest of the fields set to None.
for key in catalog_datasets_dict[hostname]:
    if len(catalog_datasets_dict[hostname][key]) == 0:
        # find the parent catalog reference, the parent catalog reference is the catalog_ref_dict at an unknown index.
        # we need to find the index by matching the parent catalog reference to the catalog reference in the catalog_refs_dict.
        index = [i for i, d in enumerate(catalog_refs_dict) if d['catalog'] == key][0]
        catalog_datasets_dict[hostname][key].append({
            "name": None,
            "catalog": key,
            "type": None,
            "server_location": None,
            "tds_path": None,
            "tds_id": None,
            "parent_catalog": catalog_refs_dict[index]['parent'],
            "mount_path": None,
            "writeable": None
        })

# pretty print catalog_datasets
# print(json.dumps(catalog_datasets_dict, indent=4))

# write json to file: tds_datasets.json
with open(f'output/{hostname}_tds_datasets.json', 'w') as f:
    json.dump(catalog_datasets_dict, f, indent=4)

print(f'Json output to: output/{hostname}_tds_datasets.json')

# write missing datasets to file: missing_datasets.json
with open(missing_datasets, 'w') as f:
    json.dump(missing_datasets_dict, f, indent=4)

# write web catalog references to file: web_catalog_refs.json
with open(web_catalog_refs, 'w') as f:
    json.dump(web_catalog_refs_dict, f, indent=4)
