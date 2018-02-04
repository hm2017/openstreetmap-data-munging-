import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

osm_file = open("dublin_ireland.osm", "r")

postcode_type_re = re.compile(r'\b\S+\.?', re.IGNORECASE)
postcode_types = defaultdict(set)

expected = ['D01','D02','D03','D04','D05','D06','D07','D08','D09','D10','D11','D12','D13','D14','D15','D16','D17','D18','D19',
           'D20','D21','D22','D23','D24','A94','A96','A98','D6W','K67', 'Dublin']

def audit_postcode_type(postcode_types, postcode):
    """ 
        Creates a list of streets not in expected list 
        
        Args:
            street_types: Set containing unexpected stree types
    """
    m = postcode_type_re.search(postcode)
    if m:
        postcode_type = m.group()
        if postcode_type not in expected:
            postcode_types[postcode_type].add(postcode)

def is_postcode(elem):
    """ 
        Checks if attribute is a street 
        Args:
            elem: Element from OpenStreetMap data
        Returns:
            True if a valid street name. False otherwise.
    """
    return (elem.attrib['k'] == "addr:postcode")

def audit():
    """ Parses through document and audits the tags for street names """
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_postcode(tag):
                    audit_postcode_type(postcode_types, tag.attrib['v'])
    pprint.pprint(dict(postcode_types))

if __name__ == '__main__':
    audit()