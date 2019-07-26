#!/usr/local/bin/python3

# ****
# Lawrence Berkeley National Lab
#
# Example of how to query all the publications of a specified 
# user from Symplectic Elements
#
# David Jacobowitz // dgj@lbl.gov
#
# v0.1 2/8/2016
# ****

import requests
import xml.etree.ElementTree as etree
from io import StringIO
import json
from collections import defaultdict
import d2xml

class VerySimpleCachedFetcher:

    def __init__(self,args):
        self.d2xml = d2xml.d2xml()
        self.loaded = False
        self.dirty = False
        self.file_name = ''
        self.cache = {}
        self.file_name = args.get('cachefile','fetch_cache.json')
        self.config_file = args.get('credfile','cdl_config.json')
        with open(self.config_file,'r') as fh:
            self.config = json.load(fh)


    def __del__(self):
        # this cannot work reliably because python is ridiculous
        # and by the time del is called, a lot of globals, 
        # things like "open", may already be gone
        self.save()

    def load(self):
        try:
            with open(self.file_name,'r') as fh:
                self.cache = json.load(fh)
                self.loaded = True
                self.dirty = False
        except Exception as e:
            print("Exception loading from: " + self.file_name)
            print(e)
        

    def save(self):
        if self.dirty:
            try:
                with open(self.file_name,'w') as fh:
                    fh.write(json.dumps(self.cache))
                    self.dirty = False
            except Exception as e:
                print("Exception saving to " + self.file_name)
                print(e)

    def _retrieve(self,name):
        if name in self.cache:
            return self.cache[name]
        return None

    def _store(self,name,thing):
        self.dirty = True
        self.cache[name] = thing





    def fetch(self,url_rest, remove_namespace=True):
        v = self._retrieve(url_rest)
        if v is not None:
            return v
        v = self._fetch(url_rest, remove_namespace)
        if v is not None:
            self._store(url_rest,v)
        return v



    def delete(self, url_rest):
        remove_namespace = True

        try:
            complete_url = self.config['url_base'] + url_rest
            print('DELETE of ' + complete_url)
            r = requests.delete(complete_url, auth = (self.config['user'],self.config['password']))
            return r.status_code
        except Exception as e:
            return 'req_failed'


    def post(self, url_rest, data, topname):
        xstring = "<?xml version='1.0' encoding='utf-8' ?>\n"
        xstring += self.d2xml.makeString(data,topname,'utf-8').decode('utf-8')
        headers = { 'Content-Type': 'text/xml' }
        remove_namespace = True
        try:
            complete_url = self.config['url_base'] + url_rest
            print('POST to ' + complete_url)
            # print(xstring)
            r = requests.post(complete_url, data = xstring, headers = headers, auth = (self.config['user'],self.config['password']))
            try:
                it = etree.iterparse(StringIO(r.text))
                if remove_namespace:
                    for _, el in it:
                        if '}' in el.tag:
                            el.tag = el.tag.split('}',1)[1]
                root = it.root
                return self.etree_to_dict(root)
            except Exception as e:
                print('Parse exception')
                print(e)
        except Exception as e:
            print('Exception')
            print(f)


    # fetches from the CDL and returns the result as a dictionary
    # (not as XML) with namespace stuff removed (for convenience)
    def _fetch(self,url_rest, remove_namespace=True):
        try:
            complete_url = self.config['url_base'] + url_rest
            print('GET from ' + complete_url)
            r = requests.get(complete_url, auth = (self.config['user'],self.config['password']))

            try:
                it = etree.iterparse(StringIO(r.text))
                if remove_namespace:
                    for _, el in it:
                        if '}' in el.tag:
                            el.tag = el.tag.split('}',1)[1]
                root = it.root
                return self.etree_to_dict(root)
                
            except Exception as e:
                print('Parse Exception')
                print(e)
        except Exception as f:
            print('Exception')
            print(f)

        return None


    
    ## Stolen from 
    ## http://stackoverflow.com/questions/7684333/converting-xml-to-dictionary-using-elementtree
    def etree_to_dict(self,t):
        d = {t.tag: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = defaultdict(list)
            for dc in map(self.etree_to_dict, children):
                for k, v in dc.items():
                    dd[k].append(v)
            d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.items()}}
        if t.attrib:
            d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                  d[t.tag]['#text'] = text
            else:
                d[t.tag] = text
        return d
