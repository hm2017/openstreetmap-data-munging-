import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

osm_file = open("dublin_ireland.osm", "r")

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
street_types = defaultdict(set)

expected = ['Street', 'Avenue', 'Court', 'Copse','Square', 'Lane', 'Road', 'Abbey', 'Close','Centre', 'Chase', 'Cottages', 'Crescent','Dale',
           'Downs','Drive','East','Estate','Gardens','Glade','Glen','Green','Grove','Hall','Heath','Heights','Hill','Lawn','Lawns','Lodge',
           'Lower','Manor','North','Oaks','Parade','Park','Place','Quay','Rise','Row','South','Terrace','Upper','Vale','View',
           'Villas','Walk','Way','Wood','Woods','West','Valley','Mews','Meadows','Meadow','Garth','Extension']

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

def audit():
    """ Parses through document and audits the tags for street names """
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    pprint.pprint(dict(street_types))

if __name__ == '__main__':
    audit()