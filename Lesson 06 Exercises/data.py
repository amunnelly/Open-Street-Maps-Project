# -*- coding: utf-8 -*-
"""
Created on Sun Jul 26 17:37:44 2015

@author: anthonymunnelly
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
import time

"""
Your task is to wrangle the data and transform the shape of the 
data
into the model we mentioned earlier. The output should be a list
 of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call
 the function with the element
as an argument. You should return a dictionary, containing the
 shaped data for that element.
We have also provided a way to save the data in a file, so that
 you could use
mongoimport later on to import the shaped data into MongoDB. 

Note that in this exercise we do not use the 'update street name'
 procedures
you worked on in the previous exercise. If you are using this code in your final
project, you are strongly encouraged to use the code from previous exercise to 
update the street names before you save them to JSON. 

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" 
and "way"
- all attributes of "node" and "way" should be turned into 
regular key/value pairs, except:
    - attributes in the CREATED array should be added under
    a key "created"
    - attributes for latitude and longitude should be 
    added to a "pos" array,
      for use in geospacial indexing. Make sure the values 
      inside "pos" array are floats
      and not strings. 
- if second level tag "k" value contains problematic 
characters, it should be ignored
- if second level tag "k" value starts with
 "addr:", it should be added to a dictionary "address"
- if second level tag "k" value does not start 
with "addr:", but contains ":", you can process it
  same as any other tag.
- if there is a second ":" that separates the type/direction of 
a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]
"""


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def shape_element(element):
    node_prime = {} # The initial collection dict
    created = {} # to create the 'created' sub-dict in the final node dict
    address = {} # to create the 'address' sub-dict in the final node dict
    pos = [0,0]
    node_refs = []
    if element.tag == "node" or element.tag == "way":
        if element.get('lat'):
            pos[0] = float(element.get('lat'))
            pos[1] = float(element.get('lon'))
            node_prime['pos'] = pos
            
        node_prime['id'] = element.get('id')
        node_prime['type'] = element.tag
        node_prime['visible'] = element.get('visible')

        created['version'] = element.get('version')
        created['changeset'] = element.get('changeset')
        created['timestamp'] = element.get('timestamp')
        created['user'] = element.get('user')
        created['uid'] = element.get('uid')

        node_prime['created'] = created

        for item in element.iter('tag'):

            # skip data that contains more than one colon
            if item.get('k').count(':') > 1:
                continue

            # format the addresses correctly
            if str(item.get('k'))[:5] == 'addr:':
                splitter = str(item.get('k')).split(':')
                address[splitter[-1]] = item.get('v')
                
            node_prime[item.get('k')] = item.get('v')

        for item in element.iter('nd'):
            node_refs.append(item.get('ref'))

        # add address dict and node_refs list if they exist
        if address != {}:
            node_prime['address'] = address
        if node_refs != []:
            node_prime['node_refs'] = node_refs

        '''
        It's not possible to remove values from a list by iterating
        through it and removing as you go in one pass. Therefore,
        we create two lists, keys_prime and keys. We iterate through
        keys_prime, checking each iteration for validity before
        adding or rejected it to the final keys list.
        We then iterate through the approved keys and use that to
        fill the final nodes dict, which is what is returned by the
        function.
        '''
        keys_prime = node_prime.keys()
        keys = []
        for key in keys_prime:
            if re.search(problemchars, key):
                pass
            if key[:5] != 'addr:':
                keys.append(key)
                
        node = {}
        for key in keys:
            node[key] = node_prime[key]
        
        return node
    else:
        return None


def process_map(file_in, pretty = False):
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def test():
    # NOTE: if you are running this code on your computer, with a larger dataset, 
    # call the process_map procedure with pretty=False. The pretty=True option adds 
    # additional spaces to the output, making it significantly larger.
    data = process_map('example3.osm', True)
    pprint.pprint(data[0])
    
    correct_first_elem = {
        "id": "261114295", 
        "visible": "true", 
        "type": "node", 
        "pos": [41.9730791, -87.6866303], 
        "created": {
            "changeset": "11129782", 
            "user": "bbmiller", 
            "version": "7", 
            "uid": "451048", 
            "timestamp": "2012-03-28T18:31:23Z"
        }
    }
    assert data[0] == correct_first_elem
    assert data[-1]["address"] == {
                                    "street": "West Lexington St.", 
                                    "housenumber": "1412"
                                      }
    assert data[-1]["node_refs"] == [ "2199822281", "2199822390",  "2199822392", "2199822369", 
                                    "2199822370", "2199822284", "2199822281"]




if __name__ == "__main__":
    test()
