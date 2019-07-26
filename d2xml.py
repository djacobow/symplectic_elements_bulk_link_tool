#!/usr/bin/env python3

# simple class to convert dicts to xml. supports attribs named '@'
# and arrays
# -- dgj@lbl.gov

import xml.etree.ElementTree as etree
import json

class d2xml:

    def __init__(self):
        pass

    def makeElem(self,data,topname):
        top = etree.Element(topname)
        self.addContents(top,data)
        return top 

    def makeString(self,data,topname,encoding='utf-8'):
        e = self.makeElem(data,topname)
        return etree.tostring(e,encoding=encoding)

    def addContents(self,parent,data):
        if isinstance(data,str):
            parent.text = data

        elif isinstance(data, list):
            for elem in data:
                newelem = etree.SubElement(parent, 'item')
                self.addContents(newelem,elem)

        elif isinstance(data,dict):
            for key in data:
                if (len(key)):
                    if key[0] == '@':
                        kn = key[1:]
                        parent.set(kn,data[key])
                    else:
                        newelem = etree.SubElement(parent, key)
                        self.addContents(newelem, data[key])



if __name__ == '__main__':

    x = {
        'foo': {
            'a': 'aaa',
            '@b': 'bbb',
            'c': {
                'x': 'xxx',
            }
        },
        '@bar': 'hi there!',
        'baz': [
            'alpha','bravo','charlie',
        ],
        'whoop': [
            {
                'dee': 'doo', '@blee': 'zinnggy',
            }
        ]
    }


    d2 = d2xml()

    print(d2.makeString(x,"things"))

