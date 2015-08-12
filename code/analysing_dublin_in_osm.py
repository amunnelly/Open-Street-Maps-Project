# -*- coding: utf-8 -*-
"""
Created on Sat Jul 25 21:26:36 2015

@author: anthonymunnelly
"""

import xml.etree.cElementTree as ET
import re
import datetime
from collections import defaultdict
import codecs
import json
from bs4 import BeautifulSoup
import urllib

an_post_url = "https://www.anpost.ie/AnPost/AnPostDM/ProductsAndServices/Publicity+Post/DublinDeliveryZones/Dublin+Delivery+Zones.htm"
postal_districts = urllib.urlretrieve(an_post_url, "postal_districts.html")

with open('satellite_towns.json', 'r') as f:
    towns = json.load(f)
    
satellite_towns = defaultdict(set)
for t in towns:
    for key, value in t.iteritems():
        satellite_towns[key] = value

def find_dublin_postcodes(postal_districts):
    '''
    (urllib object) -> dict
    '''
    postcodes_list = []
    postcodes = {}
    postcode_format = re.compile('D[0-9]{1,2}W{0,1}\.[0-9]')
    with open("postal_districts.html", "r") as f:
        soup = BeautifulSoup(f)
        tables = soup.find_all('table')
        rows = tables[1].find_all('tr')
        for r in rows[1:]:
            # rows[:1] rather than rows to skip the headings
            data = r.find_all('td')
            code = re.search(postcode_format, data[1].text)
            if code:
                current_code = code.group(0)
                current_code = current_code.split('.')
                current_code = current_code[0]
                for item in data[-2].contents:
                    if ',' in item:
                        placenames_comma = str(item).split(',')
                        for p in placenames_comma:
                            postcodes_list.append([p, current_code])
                    elif '/' in item:
                        placenames_slash = str(item).split('/')
                        for p in placenames_slash:
                            postcodes_list.append([p, current_code])
                    else:
                        postcodes_list.append([item, current_code])
                        
    for p in postcodes_list:
        '''
        The postcode districts are encoded as both strings and 
        unicode. Therefore, I've converted them all to unicode
        for consistency.
        '''
        try:
            key = p[0].strip().encode('utf-8')
            value = p[1].strip()
            postcodes[key] = value
        except:
            pass
        
    for item in range(1,25):
        key = 'Dublin ' + str(item)
        value = 'D' + str(item)
        postcodes[key] = value
    
    # Difficult values added manually    
    postcodes['Dublin 6W'] = 'D6W'
    postcodes['Blanchardstown'] = 'D15'
    postcodes['Rathmines'] = 'D6'

    return postcodes



def find_extra_postcodes(filename, dublin_postcodes):
    '''
    (str) -> dict
    Iterates through every tag in the filename xml file and identifies
    its type. If it's a node or a way, the function iterates through
    the tag's own tags, and stores them in a counter dictionary.
    '''
    f = open(filename)
    missed_keys = {}
    for event, node in ET.iterparse(f):
        if node.tag == 'node' or node.tag == 'way':
            for item in node.iter('tag'):
                if item.get('k') == 'addr:city':
                    city = item.get('v')
                    if city not in dublin_postcodes.keys():
                        if city not in missed_keys:
                            missed_keys[city] = 1
                        else:
                            missed_keys[city] += 1
                        
    return missed_keys
    

def tag_collector(filename):
    '''
    (str) -> (dict)
    Iterate through all the tags in the xml filename file, and return
    them as a dictionary whose keys are tags and values are the counts
    of those tags.
    '''
    f = open(filename)
    tags = {}
    for element, node in ET.iterparse(f):
        if node.tag not in tags:
            tags[node.tag] =1
        else:
            tags[node.tag] += 1
    f.close()
    
    return tags
    

def dictionary_sorter(tags):
    '''
    (dict)->dict
    Takes a dictionary of key counts and returns one where the
    keys are the counts in order
    '''
    counter_list = sorted(tags.values(), reverse=False)
    counters = {}
    for c in counter_list:
        for key, value in tags.iteritems():
            if c == value:
                counters[str(c)] = key
                
    for c in counter_list:
        print "{}\t{}".format(c, counters[str(c)])

    return counters
    

def key_collector(filename):
    '''
    (str) -> dict
    Iterates through every tag in the filename xml file and identifies
    its type. If it's a node or a way, the function iterates through
    the tag's own tags, and stores them in a counter dictionary.
    '''
    f = open(filename)
    keys = {}
    for event, node in ET.iterparse(f):
        if node.tag == 'node' or node.tag == 'way':
            for item in node.iter('tag'):
                sought = str(item.get('k')).strip()
                if sought not in keys:
                    keys[sought] = 1
                else:
                    keys[sought] += 1
                    
    return keys
    

def key_inspector(filename, key):
    '''
    (str, str) -> dict
    Iterates through every tag in the filename xml file and identifies
    its type. If it's a node or a way, the function iterates through
    the tag's own tags, and stores them in a counter dictionary.
    '''
    f = open(filename)
    keys = {}
    for event, node in ET.iterparse(f):
        if node.tag == 'node' or node.tag == 'way':
            for item in node.iter('tag'):
                if item.get('k') == key:
                    if item.get('v') not in keys:
                        keys[item.get('v')] = 1
                    else:
                        keys[item.get('v')] += 1
                    
    return keys

    
def audit_street_type(list_of_streets, position):
    street_types = defaultdict(set)
    if position == 'front':
        street_type_re = re.compile(r'^\S+\.?\b', re.IGNORECASE)
    else:
        street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
    for street_name in list_of_streets:
        m = street_type_re.search(street_name)
        if m:
            street_type = m.group()
            street_types[street_type].add(street_name)
    
    return street_types
    
    
def shape_element(element):
    problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
    node_prime = {} # The initial collection dict
    created = {} # to create the sub-dict in the final node dict
    address = {} # to create the sub-dict in the final node dict
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
            if item.get('k').count(':') > 1: # More than two colons
                continue

            '''Wranging the addr: fields '''
            if str(item.get('k'))[:5] == 'addr:':
                splitter = str(item.get('k')).split(':')

                # The postcode problem
                if splitter[-1] == 'city':
                    city_fix = fix_postcode(item, dublin_postcodes, satellite_towns)
                    if city_fix:
                        for key, value in city_fix.iteritems():
                            address[key] = value
                    else:
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


    
def fix_postcode(item, dublin_postcodes, satellite_towns):
    '''
    (xml object) -> dict
    The addr:city keys are in three types. This function identifies
    which function they are, and returns a dictionary appropriate
    to correct filling of the address dictionary that will become
    part of each entry dictionary.
    '''
    city = item.get('v')
    
    if city in dublin_postcodes:
        if 'Dublin' in city:
            return {"postcode":dublin_postcodes[city]}
        else:
            return {"district":city, "postcode":dublin_postcodes[city]}
    
    elif city in satellite_towns:
        return {"town":city, "county":satellite_towns[city]}

    else:
        return None


def process_map(file_in, pretty = False):
    '''
    (str, bool) -> list
    '''
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

    
def timer(start):
    '''
    (datetime object) -> None
    It's interesting to know how long it takes to convert the .xml
    to .json. This function does that.
    '''
    snap = datetime.datetime.now()
    wait = snap - start
    print "That took {} seconds.".format(wait.total_seconds())

    return

if __name__ == '__main__':
    start = datetime.datetime.now()
    # 1. Fill the postcode list
    dublin_postcodes = find_dublin_postcodes(postal_districts)
    # 2. Convert the xml data to .json
    process_map('dublin_ireland.osm')
    # 3. Time the operation
    timer(start)    