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
    args['users'] = []

    inargs = sys.argv

    for i in range(len(sys.argv)):
        arg = sys.argv[i]
        if re.match(r'-h',arg):
            args['help'] = True
        elif re.match(r'-d',arg):
            args['debug'] = True
        elif re.match(r'-f',arg):
            args['fake'] = True
        elif re.match(r'-jr',arg):
            i += 1
            arg = sys.argv[i]
            args['jsoutfile'] = arg
        elif re.match(r'-pw',arg):
            i += 1
            arg = sys.argv[i]
            args['credfile'] = arg
        elif re.search(r'\@',arg):
            args['users'].append(arg)


    if 'jsoutfile' not in args:
        args['jsoutfile'] = 'results.json'
    if 'credfile' not in args:
        args['credfile'] = 'cdl_config.json'
    if 'cachefile' not in args:
        args['cachefile'] = 'fetch_cache.json'
    if 'fake' not in args:
        args['fake'] = False

    return args

def getHelp():
    s = """

rejector.py   [ -jr <json_result_file_name> ]
              [ -pw <cred_file_name> ]
              [ -fake ]
              [ -debug ]
              [ -help ]
              user1 user2 user3 ... usern


   This tool takes a list of users (by email address) and rejects all
their suggested pubs.

It will generate output files that contains the results of the 
reject attempts.

The cred file is a json file with the credentials to access the CDL
database.

  -fake  :  Causes it to look up the necessary bits of information,
            but not actually make any changes

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


def elaboratePendingLinks(sapi, users):
    all_pending_links = {}
    for user in users:
        user_pending_links = sapi.getListOfPendingRelationships(user['id'])
        for link_id in user_pending_links:
            all_pending_links[link_id] = user_pending_links[link_id]
            all_pending_links[link_id]['user'] = user
    return all_pending_links



def deletePendingLinks(sapi, links):
    i = 0;
    for linkid in links:
        links[linkid]['result'] = sapi.removePending(linkid)


if __name__ == '__main__':
    args = readArgs()

    if 'help' in args or len(args['users']) == 0:
        print(getHelp())
        sys.exit()

    sapi = sympl_api_highlevel.SymplecticAPI(args)

    users = getUserIDs(sapi,args['users'])

    pending_links = elaboratePendingLinks(sapi,users)

    if not args['fake']:
        print('-info- running actions')
        deletePendingLinks(sapi, pending_links)

    debughelpers.dumpJS(pending_links,args['jsoutfile'])

    sapi.saveCache()

