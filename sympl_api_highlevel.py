#!/usr/local/bin/python3

# ****
# Lawrence Berkeley National Lab
#
# Example of how to associate a pub with a user and 
# associate a pub with a grant.
#
# David Jacobowitz // dgj@lbl.gov
#
# v0.1 6/5/2017
# ****


import re
import urllib.parse
import sympl_api_lowlevel as fapi
import debughelpers

class Paginator:
    def __init__(self):
        self.curr = 1
        self.last = -1

    def more(self):
        return self.curr != self.last

    def current(self):
        return self.curr

    def update(self,data):
        pagination = data['feed']['pagination']
        for page in pagination['page']:
            if page['@position'] == 'last':
                self.last = int(page['@number'])
                if self.curr != self.last:
                    self.curr += 1



class SymplecticAPI:
    def __init__(self,args):
        self.args = args
        fetcher = fapi.VerySimpleCachedFetcher(args)
        fetcher.load()
        self.fetcher = fetcher
        self.grantData = None
        self.relationTypeData = None
        self.inited = True


    def post(self, url_rest, data, topname):
        return self.fetcher.post(url_rest, data, topname)

    def delete(self, url_rest):
        return self.fetcher.delete(url_rest)


    def removePending(self, relid):
        url = 'suggestions/relationships/' + str(relid)
        return self.delete(url)


    def getUserInfo(self, uid):
        url = 'users/' + uid
        data = self.fetcher.fetch(url)
        return data

    # takes an email address, returns the system user id for that person,
    # if it exists
    def obtainUserID(self, email):
        url = 'users?' + urllib.parse.urlencode({'username':email})
        data = self.fetcher.fetch(url)
        debughelpers.debugJS(data)
        userid = None
        try:
            userid = data['feed']['entry']['object']['@id']
        except Exception as e:
            # in case there are no relationships to report
            print('Exception getting user id')
            print(e)
        
        return userid 


    def __getListOfGrants(self,fields_to_capture):
        pg = Paginator()
        items_per_page = 25

        grants = {}
        while pg.more():
            url = 'grants?' + urllib.parse.urlencode({
                'detail': 'full',
                'per-page': items_per_page,
                'page': pg.current(),
            })
            data = self.fetcher.fetch(url)

            for entry in data['feed']['entry']:
                # debughelpers.debugJS(entry)
                obj = entry['object']
                record = obj['records']['record']

                if isinstance(record,list):
                    for subrecord in record:
                        if subrecord['@source-name'] == 'source-3':
                            record = subrecord
                            break

                grantid = obj['@id']

                if grantid not in grants:
                    grants[grantid] = {}
                for field in record['native']['field']:
                    fname = field['@name']
                    if fname in fields_to_capture:
                        fval = field['text']
                        grants[grantid][fname] = fval


            pg.update(data)
           
        # print(grants)
        return grants


    def getUsersProfessionalActivityRelationships(self,uid):
        pg = Paginator()
        items_per_page = 25
        related_profas = {}
        while pg.more():
            url = 'users/' + uid + '/relationships?' + urllib.parse.urlencode({
                '@category': 'activity',
                'page': pg.current(),
            })
            data = self.fetcher.fetch(url)

            entries = []
            try:
                entries = data['feed']['entry']
            except Exception as e:
                return related_profas 

            if isinstance(entries,dict):
                entries = [ entries ]


            for entry in entries:
                relationship = entry['relationship']
                related = relationship['related']
                related_object = related['object']
                category = related_object['@category']
                rel_id = relationship['@id']
                if category == 'activity':
                    debughelpers.debugJS(relationship)
                    related_profas[rel_id] = relationship

            pg.update(data)
        return related_profas




    def getListOfPubsQuery(self,q):
        pg = Paginator()
        items_per_page = 25

        pubids = {}
        while pg.more():
            url = 'publications?' + urllib.parse.urlencode({
                'query': q,
                'page': pg.current(),
            })

            data = self.fetcher.fetch(url)
            entries = []
            try:
                entries = data['feed']['entry']
            except Exception as e:
                return pubids

            if isinstance(entries,dict):
                entries = [ entries ]

            for entry in entries:
                # debughelpers.debugJS(entry)
                obj = entry['object']
                pubid = obj.get('@id')
                if pubid is not None:
                    pubids[pubid] = {
                        'type':  obj.get('@type'),
                        'title': entry.get('title')
                    }

            pg.update(data)
            
        return pubids



    def getPubRelationships(self, pubid):
        url = 'publications/' + str(pubid) + '/relationships'
        data = self.fetcher.fetch(url)
        # debughelpers.debugJS(data)

        try:
            entries = data['feed']['entry']
        except Exception as e:
            # in case there are no relationships to report
            return []

        if isinstance(entries,dict):
            entries = [ entries ]

        relres = []

        for entry in entries:
            rel = entry['relationship']
            relres.append({
                'typeid'    : rel.get('@type-id'),
                'typename'  : rel.get('@type'),
                'own_id'    : rel.get('@id'),
                'related_id': rel['related'].get('@id'),
            })

        return relres 

    def checkRelationshipExists(self, rels, relid, reltype):
        for rel in rels:
            id_match   = relid == rel['related_id']
            type_match = reltype == rel['typeid']
            if id_match and type_match:
                return True
        return False


        
    def getListOfPendingRelationships(self, userid):
        pg = Paginator()
        items_per_page = 100

        pending_links = {}
        while pg.more():
            url = ''.join(
                    ['users/',
                     userid,
                     '/suggestions/relationships/pending/publications',
                     '?',
                     urllib.parse.urlencode({
                         'per-page': items_per_page,
                         'page': pg.current(),
                     })
                    ])

            data = self.fetcher.fetch(url)

            try:
                entries = data['feed']['entry']
            except Exception as e:
                print('-info- getListOfPendingRelationships user {0} has no pending pubs'.format(str(userid)))
                entries = []

            if isinstance(entries, dict):
                entries = [ entries ]

            try:
                for entry in entries:
                    #debughelpers.debugJS(entry)
                    suggestion = entry['relationship-suggestion']
                    related = suggestion['related']
                    pending_links[suggestion['@id']] = {
                        'id': suggestion['@id'],
                        'type': suggestion['@type'],
                        'related': {
                            'id': related['@id'],
                            'title': entry['title'] 
                        },
                    }

            except Exception as e:
                pass

            pg.update(data)

        return pending_links


    # takes the system user id for a person, returns a list of the system
    # id for all the publications associated with that user
    def getListOfUsersPubIDs(self, userid):
        pg = Paginator()
        items_per_page = 25

        pubs = []
        while pg.more():

            url = ''.join(
                ['users/', str(userid),
                 '/publications?',
                 urllib.parse.urlencode({
                     'per-page': items_per_page,
                     'page': pg.current(),
                 })
                ])
            data = self.fetcher.fetch(url)
            # debughelpers.dumpJS(data, userid)

            try:
                entries = data['feed']['entry']
            except Exception as e:
                print('-warning- getListofUserPubIDs {0} has no entries'.format(str(userid)))
                entries = []

            if isinstance(entries,dict):
                entries = [ entries ]

            try:
                for entry in entries:
                    relationship = entry['relationship']
                    rtype = relationship['@type']
                    if (rtype == 'publication-user-authorship'):
                        pubid = relationship['related']['@id']
                        pubs.append(pubid)

            except Exception as e:
                pass

            pg.update(data)
        return pubs



    # takes a system publication id and returns some of the bibliographic 
    # information for the publication. This routine is by no means 
    # comprehensive. There is a lot of info available per publication in 
    # the database, and some of it varies with pub type. This just pulls a 
    # few interesting fields
    def getPubDetails(self,pubid):
        url = 'publications/' + str(pubid)
        data = self.fetcher.fetch(url)
        # debughelpers.debugJS(data)
        obj = data['feed']['entry']['object']

        pdata = {}

        try:
            rtype = obj['@type']
            pdata['type'] = rtype 
        except Exception as e:
            pass

        try:
            jtitle = obj['journal']['records']['record'][0]['title']
            pdata['journal'] = jtitle
        except Exception as e:
            pass

        # a pub can have come from more than one source nad have more 
        # than one record. Just use the first for now.
        record = obj['records']['record']
        if type(record) is list:
            record = record[0]

        fields = record['native']['field']
        # debughelpers.debugJS(fields)

        for field in fields:
            field_name = field['@name']
            if field_name in ['author-url', 'title', 'abstract', 'volume',
                              'eissn', 'issn', 'journal', 'issue', 'doi']:
                pdata[field_name] = field['text']
            elif field_name == 'publication-date':
                d = []
                for t in ['year','month','day']:
                    if t in field['date']:
                        d.append(field['date'][t])
                pdata['pub_date'] = '/'.join(d)
            elif field_name == 'pagination':
                try:
                    pdata['pages'] = {
                        'from': field['pagination']['begin-page'],
                        'to': field['pagination']['begin-page']
                    }
                except Exception as e:
                    pass

        return pdata

    def __getListOfRelationshipTypes(self):
        rids = {};
        url = 'relationship/types'
        data = self.fetcher.fetch(url)
        for entry in data['feed']['entry']:
            rt = entry['relationship-type']
            name = rt['@name']
            rid  = rt['@id']
            rids[rid] = name
        return rids


    def loadRelationshipData(self):
        if self.relationTypeData == None:
            print('-info- fetching relationship types')
            self.relationTypeData = self.__getListOfRelationshipTypes()

    def findRelationshipTypeID(self, name):

        self.loadRelationshipData()

        for relid in self.relationTypeData:
            if self.relationTypeData[relid] == name:
                return relid;
        return None


    def findRelationshipTypeIDs(self, regex):

        self.loadRelationshipData()

        relids = []
        for relid in self.relationTypeData:
            if re.search(regex,self.relationTypeData[relid]):
                relids.append(relid)
        return relids

    def loadGrantData(self):
        if self.grantData == None:
            print('-info- fetching grant data')
            self.grantData = self.__getListOfGrants(['funder-name','funder-reference'])

    def getGrantName(self,grantid):

        self.loadGrantData()

        grant = self.grantData.get(grantid)
        if grant is not None:
            return grant.get('funder-name')

        return None

    def findGrantsMatching(self, regex,fieldname):

        self.loadGrantData()

        res = []
        for grantid in self.grantData:
            fval = self.grantData[grantid].get(fieldname,'')
            require_exact_match = True
            if require_exact_match:
                if regex == fval:
                    res.append(grantid)
            else:
                m = re.search(regex,fval)
                if m:
                    res.append(grantid)
        return res

    def saveCache(self):
        self.fetcher.save()

