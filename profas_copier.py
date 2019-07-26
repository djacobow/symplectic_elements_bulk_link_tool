#!/usr/local/bin/python3

# remove all of a user's suggested pubs

import re
import urllib.parse
import sympl_api_highlevel
import debughelpers
import sys

# I loathe parseargs, sorry:
def readArgs():
    args = {}
    #args['tgt'] = 'keasling@berkeley.edu'
    #args['src'] = 'JDKeasling@lbl.gov'

    inargs = sys.argv

    for i in range(len(sys.argv)):
        arg = sys.argv[i]
        if re.match(r'-h',arg):
            args['help'] = True
        elif re.match(r'-debug',arg):
            args['debug'] = True
        elif re.match(r'-dry',arg):
            args['dry'] = True
        elif re.match(r'-rm',arg):
            args['remove'] = True
        elif re.match(r'-pw',arg):
            i += 1
            args['credfile'] = sys.argv[i]
        elif re.match(r'-src',arg):
            i += 1
            args['src'] = sys.argv[i]
        elif re.match(r'-tgt',arg):
            i += 1
            args['tgt'] = sys.argv[i]

    if 'credfile' not in args:
        args['credfile'] = 'cdl_config.json'
    if 'cachefile' not in args:
        args['cachefile'] = 'fetch_cache.json'
    if 'dry' not in args:
        args['dry'] = False 
    if 'remove' not in args:
        args['remove'] = False 

    return args

def getHelp():
    s = """

profas_pusher.py 
      -src <email of user to copy FROM>
      -tgt <email of user to copy TO>
    [ -jr <json_result_file_name> ]
    [ -pw <cred_file_name> ]
    [ -dry ]
    [ -rm ]
    [ -debug ]
    [ -help ]


   This tool copies all the professional activities of the "source user"
to the "target user". This tool was developed to allow the migration of 
data from one account to another when two accounts were created erroneously
and one of the accounts got all the data.

It will generate output files that contains the results of the 
reject attempts.

The cred file is a json file with the credentials to access the CDL
database.

  -dry   :  Causes it to look up the necessary bits of information,
            but not actually make any changes

  -rm    :  Causes the old existing links to be removed

  -debug :  Turns on debugspew

  -help  :  Print this message

    """
    return s



def getUserIDs(sapi, emails):
    uids = []
    for email in emails:
        uid = sapi.obtainUserID(email)
        if uid is not None:
            uids.append({'email':email,'id':uid})
        else:
            print('Could not locate user id for: ' + email)
    return uids


def croak(s):
    print('-error- ' + s)
    sys.exit()



def prepareLinksForDeletion(srcrels):
    rv = []
    for relid in srcrels:
        srcrel = srcrels[relid]
        r = {
            'url': 'relationships/' + srcrel['@id']
        }
        rv.append(r)
    return rv

def prepareNewLinks(userid, srcrels):
    rv = []
    for relid in srcrels:
        srcrel = srcrels[relid]
        related_object = srcrel['related']['object']
        object_id = related_object['@id']
        r = {
            'topname': 'import-relationship',
            'url': 'relationships',
            'payload': {
                '@xmlns': 'http://www.symplectic.co.uk/publications/api',
                'from-object': 'activity(' + object_id + ')',
                'to-object': 'user(' + userid + ')',
                'type-id': srcrel['@type-id'],
            },
        }
        rv.append(r)
    return rv

def createNewLinks(sapi, work_to_do):
    count = 0
    for thing in work_to_do:
        res = sapi.post(thing['url'],thing['payload'],thing['topname'])
        thing['create_result'] = res
        count += 1


def deleteOldLinks(sapi, work_to_do):
    count = 0
    for thing in work_to_do:
        res = sapi.delete(thing['url'])
        thing['del_result'] = res
        count += 1


if __name__ == '__main__':
    args = readArgs()

    if 'help' in args:
        print(getHelp())
        sys.exit()

    sapi = sympl_api_highlevel.SymplecticAPI(args)

    src_users = getUserIDs(sapi,[ args['src'] ])
    tgt_users = getUserIDs(sapi,[ args['tgt'] ])

    if not len(src_users):
        croak('-error- source user ' + args.get('srcuser','<missing>') + ' not found')
    if not len(tgt_users):
        croak('-error- target user ' + args.get('tgtuser','<missing>') + ' not found')

    src_id = src_users[0]['id']
    tgt_id = tgt_users[0]['id']

    related_profas = sapi.getUsersProfessionalActivityRelationships(src_id)

    if True:
        work_to_do     = prepareNewLinks(tgt_id, related_profas)

        if args['dry']:
            debughelp.debugJS(work_to_do)
        else:
            createNewLinks(sapi, work_to_do)

    if True:
        work_to_do     = prepareLinksForDeletion(related_profas)
        if args['dry']:
            debughelpers.debugJS(work_to_do)
        elif args['remove']:
            deleteOldLinks(sapi, work_to_do)

    if args.get('debug',False):
        debughelpers.debugJS(work_to_do)

    sapi.saveCache()

