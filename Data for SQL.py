import csv
import codecs
import re
import xml.etree.cElementTree as ET
import cerberus
import schema

import ImprovingStreetNames 
import ImprovingPostcodeNames

OSM_PATH = "dublin_ireland.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

def tag_dictionary(element, secondary, default_tag_type):
    """
        Imports element and creates a tag dictionary. Updates the 
        street names and postal codes to create uniform dictionary.
        Args:
            element: An element from the OpenStreetMap data.
            secondary: Child element of the element.
            default_tag_type: Set to 'regular'
        Returns:
            new: New dictionary of tags.
    """
    new = {}
    new['id'] = element.attrib['id']
    if ":" not in secondary.attrib['k']:
        new['key'] = secondary.attrib['k']
        new['type'] = 'regular'
    else:
        after_colon = secondary.attrib['k'].index(":") + 1
        new['key'] = secondary.attrib['k'][after_colon:]
        new['type'] = secondary.attrib['k'][:after_colon - 1]
    
    value = secondary.attrib['v']
    
    if secondary.attrib['k'].startswith('addr:') == 1 and secondary.attrib['k'].count(':') < 2:
        field = secondary.attrib['k'][5:]
        if field == 'street':
            value = ImprovingStreetNames.update_street_name(secondary.attrib['v'])
        elif field == 'postcode':
            value = ImprovingPostcodeNames.update_postcode(secondary.attrib['v'])
    
    if isinstance(value, basestring):
        new['value'] = value
    else:
        new['value'] = str(value)

    return new

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """
        Clean and shape node or way XML element to Python dict
    
        Args:
            element: Element from the OpenStreetMap data.
            node_attr_fields: Predefined node tags in NODE_FIELDS
            way_attr_fields: Predefined way tags in WAY_FIELDS
            problem_chars: Regular expression searching for problem chars
            default_tag_type: set to 'regular'
        Returns:
            Dictionar for either the node attributes, way attributes, or way nodes
    """

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        for name, value in element.attrib.items():
            if name in node_attr_fields:
                node_attribs[name] = value

        for secondary in element.iter():
            if secondary.tag == 'tag':
                if problem_chars.match(secondary.attrib['k']) is not None:
                    continue
                else:
                    new_dict = tag_dictionary(element, secondary, default_tag_type)
                    if new_dict is not None:
                        tags.append(new_dict)
        return {'node': node_attribs, 'node_tags': tags}

    elif element.tag == 'way':
        for name, value in element.attrib.items():
            if name in way_attr_fields:
                way_attribs[name] = value

        counter = 0
        for secondary in element.iter():
            if secondary.tag == 'tag':
                if problem_chars.match(secondary.attrib['k']) is not None:
                    continue
                else:
                    new_dict = tag_dictionary(element, secondary, default_tag_type)
                    if new_dict is not None:
                        tags.append(new_dict)
            elif secondary.tag == 'nd':
                newnd = {}
                newnd['id'] = element.attrib['id']
                newnd['node_id'] = secondary.attrib['ref']
                newnd['position'] = counter
                counter += 1
                way_nodes.append(newnd)
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

 

 # ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """
        Parses through file and gets specified elements.
        Args: 
            osm_file: OpenStreetMap data
            tags: The three tags of interest; node, way, and relation.
        Yield:
            Yield element if it is the right type of tag
    """

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """
        Validates each element according to schema.
        Args:
            element: An element from the OpenStreetMap data
            validator: The cerberus validator
            schema: The desired format 'SCHEMA'
        
        Raises:
            Raise ValidationError if element does not match schema
    """
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """
        Iteratively process each XML element and write to csv(s)
        Args: 
            file_in: The OpenStreetMap data
            validate: The cerberus validator
    """

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower
    process_map(OSM_PATH, validate=True)

