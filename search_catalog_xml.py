
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
        print(f'Error: Could not find catalog references in {catalog_ref}')
        catalog_refs = []
    return catalog_refs

def updateCatalogRefs(catalog_refs):
    catalog_refs_sublist = []
    for catalog_ref in catalog_refs:
        # remove the thredds_home_dir from the catalog_ref
        catalog_ref_rel_path = Path(catalog_ref).relative_to(thredds_home_dir)
        # remove the catalog.xml file name from the relative path
        catalog_ref_rel_path = catalog_ref_rel_path.parent
        # join the thredds_home_dir with the relative path
        catalog_path = thredds_home_dir / catalog_ref_rel_path
        catalog_ref_xml = ET.parse(catalog_ref)
        catalog_refs_sublist += getCatalogRefs(catalog_ref_xml, catalog_ref, catalog_path)

    return catalog_refs_sublist

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
catalog_refs = getCatalogRefs(catalog_xml, catalog_ref, thredds_home_dir)

# for each catalog reference, read the catalog file, and parse it for additional catalog references. add these to the list of catalog references.
# run updateCatalogRefs until there are no additional sub catalog references.
n = 0
catalog_refs_sublist= updateCatalogRefs(catalog_refs)
while len(catalog_refs_sublist) > 0:
    # Update catalog reference list with sublist n.
    catalog_refs += catalog_refs_sublist
    n+=1
    print(f'\nFound nested catalogs\n Parsing nested catalog {n}. \n')    
    # Get new sublist
    catalog_refs_sublist = updateCatalogRefs(catalog_refs_sublist)

# Update the catalog references to remove the thredds_home_dir.
catalog_refs = [str(Path(ref).relative_to(thredds_home_dir)) for ref in catalog_refs]
catalog_refs.sort()
print (catalog_refs)

# for each catalog reference, read the catalog file, and parse it to find the dataset locations.