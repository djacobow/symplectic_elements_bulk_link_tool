#!/usr/local/bin/python3

# remove all of a user's suggested pubs

import re
import urllib.parse
import sympl_api_highlevel
import debughelpers
import sys
import csvloader

# I loathe parseargs, sorry:
def readArgs():
    args = {}
    args['users'] = []

    inargs = sys.argv

    for i in range(len(sys.argv)):
        arg = sys.argv[i]
        if re.match(r'-h',arg):
            args['help'] = True
        elif re.match(r'-i',arg):
            i += 1
            args['infile'] = sys.argv[i]
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


    if 'infile' not in args:
        args['infile'] = 'default.csv'
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

rejector2.py  [ -i  <csv file with things to reject ]
              [ -jr <json_result_file_name> ]
              [ -pw <cred_file_name> ]
              [ -fake ]
              [ -debug ]
              [ -help ]
              user1 user2 user3 ... usern


   This tool takes a csv file with users and dois and rejects them.

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




def elaboratePendingLinks(sapi, users):
    print('elaboratePendingLinks()')
    count = 0;
    for user in users:
        count += 1
        if 'pending_links' not in users[user]:
            users[user]['pending_links'] = {}

        eid = users[user].get('elements_id',None)
        if eid:
            user_pending_links = sapi.getListOfPendingRelationships(eid)
            for link_id in user_pending_links:
                users[user]['pending_links'][link_id] = user_pending_links[link_id]


def deletePendingLinks(sapi, users):
    i = 0;
    for user in users:
        for rej_req in users[user]['reject_requests']:
            if 'linkid' in rej_req:
                rej_req['delete_result'] = sapi.removePending(rej_req['linkid'])


def sortInputData(ind):
    results = {}
    for row in ind:
        user = row['Email']
        doi  = row['DOI']
        wos  = row['UID']
        if re.search(r'\@',user):
            if not user in results:
                results[user] = {}
                results[user]['reject_requests'] = []
            results[user]['reject_requests'].append({'doi':doi,'wos':wos})
    return results

def getUserIDs(sapi, users):
    print('getUserIDs()')
    for user in users:
        uid = sapi.obtainUserID(user)
        if uid is not None:
            users[user]['elements_id'] = uid
        else:
            print('Could not locate user id for: ' + user)
    return users


def getPubsDataViaAPI(sapi, users):
    print('getPubsDataViaAPI()')
    pubsdata = {}
    for user in users:
        print("User: " + user)
        for pending_link in users[user]['pending_links']:
            pubid = users[user]['pending_links'][pending_link]['related']['id']
            if pubid not in pubsdata:
                print('.')
                pubdata = sapi.getPubDetails(pubid)
                if 'doi' in pubdata:
                    pubsdata[pubid] = pubdata['doi']
            else:
                print('+')
        sapi.saveCache()
    return pubsdata


def invertPendings(users):
    print('invertPendings()')
    for user in users:
        if not 'pending_links_by_pub' in users[user]:
            users[user]['pending_links_by_pub'] = {}

        for linkid in users[user]['pending_links']:
            pubid = users[user]['pending_links'][linkid]['related']['id']
            users[user]['pending_links_by_pub'][pubid] = linkid

def getPubsDataViaReportingDB(files):
    print('getPubsDataViaReportingDB()')
    pubsdata = {}
    for fn in files:
        fdata = csvloader.load(fn,'tsv')
        for row in fdata:
            sid = row.get('system_id',None)
            doi = row.get('doi',None)
            if sid and doi:
                pubsdata[sid] = doi
    return pubsdata


def invertKVs(d):
    od = {}
    for k, v in d.items():
        od[v] = k
    return od


def findRejectables(users, pubs_by_doi):
    print('findRejectables()')
    rejectables = []
    for user in users:
        for rej_req in users[user]['reject_requests']:
            doi = rej_req.get('doi',None)
            if doi is not None:
                pubid = pubs_by_doi.get(doi,None)
                if pubid and len(pubid):
                    rej_req['pubid'] = pubid
                    linkid = users[user]['pending_links_by_pub'].get(pubid,None)
                    if linkid:
                        rej_req['linkid'] = linkid
                        users[user]['pending_links'][linkid]['user_requested_rejection'] = True
                        rejectables.append(linkid)
    return rejectables


if __name__ == '__main__':
    args = readArgs()

    if 'help' in args:
        print(getHelp())
        sys.exit()

    sapi = sympl_api_highlevel.SymplecticAPI(args)

    indata = csvloader.load(args['infile'])

    users  = sortInputData(indata)

    getUserIDs(sapi, users)

    elaboratePendingLinks(sapi, users)

    invertPendings(users)

    #pubsdata = getPubsDataViaAPI(sapi, users)
    pubsdata = getPubsDataViaReportingDB([
        '../reporting/raw/20170911/lbl_unclaimed_report.tsv',
        '../reporting/raw/20170911/lbl_pub_report.tsv',])
    pubs_by_doi = invertKVs(pubsdata)

    rejectables = findRejectables(users, pubs_by_doi)

    if not args['fake']:
        print('-info- running actions')
        deletePendingLinks(sapi, users)

    debughelpers.dumpJS(users,args['jsoutfile'])

    sapi.saveCache()

    sys.exit()


