
import lxml.etree as ET
from pathlib import Path

# function to get all catalogRefs in the catalog.xml file.
def getCatalogRefs(catalog_xml, catalog_ref, catalog_path):
    try:
        catalog_refs = [tag.get('{http://www.w3.org/1999/xlink}href') for tag in catalog_xml.iter() if tag.tag.endswith('catalogRef')]
        # add the catalog path to the catalog references
        catalog_refs = [catalog_path / ref for ref in catalog_refs]
        # if the catalog reference contains a directory of /../, remove the /../ and the previous directory from the path.
        catalog_refs = [Path(ref).resolve() for ref in catalog_refs]
    except:
        # print(f'No catalog references in {catalog_ref}.')
        catalog_refs = []
    return catalog_refs

# refactor the function getCatalogRefs to output a dictionary with the catalog reference and the catalog path.
def getCatalogRefs(catalog_xml, catalog_ref, catalog_path):
    try:
        catalog_refs = [tag.get('{http://www.w3.org/1999/xlink}href') for tag in catalog_xml.iter() if tag.tag.endswith('catalogRef')]
        # add the catalog path to the catalog references
        catalog_refs = [catalog_path / ref for ref in catalog_refs]
        # if the catalog reference contains a directory of /../, remove the /../ and the previous directory from the path.
        catalog_refs = [Path(ref).resolve() for ref in catalog_refs]
        # create a dictionary with the catalog reference and the catalog path.
        catalog_refs_dict = [{"parent": catalog_ref, "catalog": ref} for ref in catalog_refs]
    except:
        # print(f'No catalog references in {catalog_ref}.')
        catalog_refs = []
        catalog_refs_dict = []
    return catalog_refs, catalog_refs_dict

def updateCatalogRefs(catalog_refs):
    catalog_refs_sublist = []
    catalog_refs_sublist_dict = []
    for catalog_ref in catalog_refs:
        # remove the thredds_home_dir from the catalog_ref
        catalog_ref_rel_path = Path(catalog_ref).relative_to(thredds_home_dir)
        # remove the catalog.xml file name from the relative path
        catalog_ref_rel_path = catalog_ref_rel_path.parent
        # join the thredds_home_dir with the relative path
        catalog_path = thredds_home_dir / catalog_ref_rel_path
        catalog_ref_xml = ET.parse(catalog_ref)
        sublist, sublist_dict = getCatalogRefs(catalog_ref_xml, catalog_ref, catalog_path)
        catalog_refs_sublist += sublist
        catalog_refs_sublist_dict += sublist_dict
    return catalog_refs_sublist, catalog_refs_sublist_dict

# read /var/lib/tomcat/content/thredds/catalog.xml and parse it for additional catalog references.
# read the catalog.xml file
thredds_home_dir = Path('/var/lib/tomcat/content/thredds/')
# join the thredds_home_dir with the catalog.xml file
catalog_ref = thredds_home_dir / 'catalog.xml'
print(catalog_ref)
# catalog_ref = thredds_home_dir + 'catalog.xml'
catalog_xml = ET.parse(str(catalog_ref))

# additional catalog references are stored in the <catalogRef> tag and have a 'xlink:href' attribute for the location of the catalog.
# find all <catalogRef> tags in the catalog.xml file
catalog_refs, catalog_refs_dict = getCatalogRefs(catalog_xml, catalog_ref, thredds_home_dir)

# print (f'Catalogs before updating with sublists: {len(catalog_refs)}\n')
# print (f'Catalog dicts before updating with sublists: {len(catalog_refs_dict)}\n')

# for each catalog reference, read the catalog file, and parse it for additional catalog references. add these to the list of catalog references.
# run updateCatalogRefs until there are no additional sub catalog references.
n = 0
catalog_refs_sublist, catalog_refs_sublist_dict = updateCatalogRefs(catalog_refs)
while len(catalog_refs_sublist) > 0:
    # Update catalog reference list with sublist n.
    catalog_refs += catalog_refs_sublist
    catalog_refs_dict += catalog_refs_sublist_dict
    n+=1
    print(f'\nFound nested catalogs\n Parsing nested catalog {n}. \n')    
    # Get new sublist
    catalog_refs_sublist, sublist_dict = updateCatalogRefs(catalog_refs_sublist) 

# Update the catalog references to remove the thredds_home_dir from the catalog dictionary.
for ref in catalog_refs_dict:
    ref['catalog'] = str(Path(ref['catalog']).relative_to(thredds_home_dir))
    ref['parent'] = str(Path(ref['parent']).relative_to(thredds_home_dir))

# Sort the dictionary
catalog_refs_dict.sort(key=lambda x: x['catalog'])
print (f'Catalog dicts: {catalog_refs_dict}\n')


# create a dictionary to store the dataset locations for each catalog reference.
catalog_datasets_dict = {}
# for each catalog key in each item in the catalog_refs_dict, read the catalog file, parse it to find the dataset locations, 
# and finally add the dataset location and other attrs to the dictionary.
for catalog_ref in catalog_refs_dict:
    # create a string from catalog ref that is just the end name of the catalog reference and drop the extension
    catalog_ref_key = Path(catalog_ref['catalog']).stem
    catalog_ref_str = catalog_ref['catalog']
    # get the parent catalog reference
    catalog_ref_parent = str(catalog_ref['parent'])
    # add a key to the dictionary for the catalog reference add an empty list as the value to append each found dataset location.
    
    catalog_datasets_dict[catalog_ref_str] = []
    
    catalog_ref = thredds_home_dir / catalog_ref['catalog']
    catalog_xml = ET.parse(str(catalog_ref))
    # dataset locations are stored in the <datasetScan> and <datasetRoot> tags and have a 'location' attribute for the location of the dataset.
    for tag in catalog_xml.iter():
        try:
            if tag.tag.endswith('datasetScan') or tag.tag.endswith('datasetRoot'):
                # append the location attribute to the list of dataset locations for the catalog reference.
                catalog_datasets_dict[catalog_ref_str].append({
                    "name": tag.get('name'),
                    "catalog": str(catalog_ref),
                    "type": tag.tag.split('}')[-1],
                    "server_location": tag.get('location'),
                    "tds_path": tag.get('path'),
                    "tds_id": tag.get('ID'),
                    "parent_catalog": catalog_ref_parent
                })
        except:
            continue

# print the key 'catalog' in the catalog_refs_dict
# for key in catalog_refs_dict:
    
#     print(key['catalog'])

# iterate the keys of a dictionary

# if a key in the catalog_datasets_dict has no dataset locations, add a nested dictionary with the catalog, parent and the rest of the fields set to None.
for key in catalog_datasets_dict:
    # print (key)
    # get index of the key in the catalog_refs_dict
    # index = [i for i, d in enumerate(catalog_refs_dict) if d['catalog'] == key][0]
    # print(index)
    if len(catalog_datasets_dict[key]) == 0:
        # find the parent catalog reference, the parent catalog reference is the catalog_ref_dict at an unknown index.
        # we need to find the index by matching the parent catalog reference to the catalog reference in the catalog_refs_dict.
        index = [i for i, d in enumerate(catalog_refs_dict) if d['catalog'] == key][0]

        catalog_datasets_dict[key].append({
            "name": None,
            "catalog": key,
            "type": None,
            "server_location": None,
            "tds_path": None,
            "tds_id": None,
            "parent_catalog": catalog_refs_dict[index]['parent']
        })


# pretty print catalog_datasets
import json
print(json.dumps(catalog_datasets_dict, indent=4))
# write json to file: tds_datasets.json
with open('tds_datasets.json', 'w') as f:
    json.dump(catalog_datasets_dict, f, indent=4)
