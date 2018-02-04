import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "dublin_ireland.osm"
postcode_type_re = re.compile(r'\b\S+\.?', re.IGNORECASE)

expected = ['D01','D02','D03','D04','D05','D06','D07','D08','D09','D10','D11','D12','D13','D14','D15','D16','D17','D18','D19',
           'D20','D21','D22','D23','D24','A94','A96','A98','D6W','K67', 'Dublin']

MAPPING = { "1":"D01",
            "2": "D02",
            "3": "D03",
            "4": "D04",
            "8": "D08",
            "12": "D12",
            "13": "D13",
            "17": "D17",
            "18": "D18",
            "22": "D22",
           "D15KPW7" : "D15 KPW7",
           "D01X2P2" : "D01 X2P2",
           "D05N7F2" : "D05 N7F2",
           "D6WXK28" : "D6W XK28",
           "560068" : "",
           "0000" : "" 
          }           

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


def audit(osmfile):
    """ 
        Parses through document and audits the street tags 
        Args:
            osmfile: Data from OpenStreetMap
        Returns:
            street_types: Set containing unexpected street names
    """
    osm_file = open(osmfile, "r")
    postcode_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_postcode(tag):
                    audit_postcode_type(postcode_types, tag.attrib['v'])
    elem.clear()
    return postcode_types

def update_postcode(name, mapping=MAPPING):
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
    postcode_types = audit(OSMFILE)
    pprint.pprint(dict(postcode_types))

    for post_type, ways in postcode_types.iteritems():
        for name in ways:
            better_name = update_postcode(name, MAPPING)
        print (name, "=>", better_name)

if __name__ == '__main__':
     final()
