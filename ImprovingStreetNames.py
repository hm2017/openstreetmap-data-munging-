import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "dublin_ireland.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

expected = ['Street', 'Avenue', 'Court', 'Copse','Square', 'Lane', 'Road', 'Abbey', 'Close','Centre', 'Chase', 'Cottages', 'Crescent','Dale',
           'Downs','Drive','East','Estate','Gardens','Glade','Glen','Green','Grove','Hall','Heath','Heights','Hill','Lawn','Lawns','Lodge',
           'Lower','Manor','North','Oaks','Parade','Park','Place','Quay','Rise','Row','South','Terrace','Upper','Vale','View',
           'Villas','Walk','Way','Wood','Woods','West','Valley','Mews','Meadows','Meadow','Garth','Extension']


MAPPING = { "Ave": "Avenue",
            "Rd": "Road",
            "road": "Road",
            "lane": "Lane",
                       }           

def audit_street_type(street_types, street_name):
    """ 
        Creates a list of streets not in expected list 
        
        Args:
            street_types: Set containing unexpected stree types
    """
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def is_street_name(elem):
    """ 
        Checks if attribute is a street 
        Args:
            elem: Element from OpenStreetMap data
        Returns:
            True if a valid street name. False otherwise.
    """
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    """ 
        Parses through document and audits the street tags 
        Args:
            osmfile: Data from OpenStreetMap
        Returns:
            street_types: Set containing unexpected street names
    """
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    elem.clear()
    return street_types

def update_street_name(name, mapping=MAPPING):
    """ 
        Replaces unexpected street names with better names 
        Args:
            name: An unexpected street name
            mapping: Dictionary of expected street names
        Returns:
            name: The updated street name
    """
    words = name.split()
    for w in range(len(words)):
        if words[w] in mapping:
            words[w] = mapping[words[w]]
    name = " ".join(words)
    return name

def final():
    """ 
        Runs the functions and ouputs both the unexpected 
        street name and better street name 
    """
    st_types = audit(OSMFILE)
    pprint.pprint(dict(st_types))

    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_street_name(name, MAPPING)
        print (name, "=>", better_name)

if __name__ == '__main__':
     final()
