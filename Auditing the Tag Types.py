import xml.etree.ElementTree as ET
import pprint

OSM_file = 'dublin_ireland.osm'

def count_tags(filename):

    tags = {}
    for eva, elem in ET.iterparse(filename):
        tag = elem.tag
        if tag not in tags.keys():
            tags[tag] = 1
        else:
            tags[tag]+=1
    return tags

tags = count_tags(OSM_file)
pprint.pprint(tags)
