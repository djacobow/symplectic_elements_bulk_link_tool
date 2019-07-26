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
import sys
import csvloader
import sympl_api_highlevel
import debughelpers

# I loathe parseargs, sorry:
def readArgs():
    args = {}

    for i in range(len(sys.argv)):
        arg = sys.argv[i]
        if re.match(r'-h', arg):
            args['help'] = True
        elif re.match(r'-d', arg):
            args['debug'] = True
        elif re.match(r'-f', arg):
            args['fake'] = True
        elif re.match(r'-i', arg):
            i += 1
            arg = sys.argv[i]
            args['infile'] = arg
        elif re.match(r'-cr', arg):
            i += 1
            arg = sys.argv[i]
            args['csvoutfile'] = arg
        elif re.match(r'-jr', arg):
            i += 1
            arg = sys.argv[i]
            args['jsoutfile'] = arg
        elif re.match(r'-pw', arg):
            i += 1
            arg = sys.argv[i]
            args['credfile'] = arg
        elif re.match(r'-tab', arg):
            args['dialect'] = 'tsv'


    if 'jsoutfile' not in args:
        args['jsoutfile'] = 'results.json'
    if 'csvoutfile' not in args:
        args['csvoutfile'] = 'results.csv'
    if 'credfile' not in args:
        args['credfile'] = 'cdl_config.json'
    if 'cachefile' not in args:
        args['cachefile'] = 'fetch_cache.json'
    if 'fake' not in args:
        args['fake'] = False
    if 'dialect' not in args:
        args['dialect'] = 'csv'

    return args

def getHelp():
    s = """

link_maker.py   -infile <file_name>
              [ -jr <json_result_file_name> ]
              [ -cr <csv_result_file_name> ]
              [ -pw <cred_file_name> ]
              [ -tab ]
              [ -fake ]
              [ -debug ]
              [ -help ]

   This tool takes a CSV file containing a list of publications DOIs
combined with either usernames (LDAP) or grants names, as present in
the LBL Publications Management System. It then uses the Symplectic
API to create those links in the live publications system.

It will generate output files that contains the results of the
link attempts.

The cred file is a json file with the credentials to access the CDL
database.

  -fake  :  Causes it to look up the necessary bits of information,
            but not actually make any changes

  -debug :  Turns on debugspew

  -tab   :  Read config from a TAB delimited file. Write TAB delimited
            results. If not present, use and make .csv

  -help  :  Print this message

    """
    return s


def elaborateRequestList(rl, sapi):

    pub_rel_grant_type_id = sapi.findRelationshipTypeID('publication-grant-funded')
    pub_rel_author_type_id = sapi.findRelationshipTypeID('publication-user-authorship')

    if pub_rel_grant_type_id is None:
        print('-err- could not find grant/pub typeid')
        return
    if pub_rel_author_type_id is None:
        print('-err- could not find author/pub typeid')
        return

    for req in rl:
        req['elab_messages'] = []

        grant = req.get('grant', '')
        req['try_link_grant'] = False
        req['grantid'] = None

        if len(grant):
            matching_grants = sapi.findGrantsMatching(grant, 'funder-name')
            grant_count = len(matching_grants)
            if grant_count == 1:
                req['grantid'] = matching_grants[0]
                req['try_link_grant'] = True
                req['grant_matched_name'] = sapi.getGrantName(req['grantid'])
            elif grant_count == 0:
                req['elab_messages'].append('grant_not_found')
            else:
                req['elab_messages'].append('multiple_matching_grants: ' +
                        ', '.join(matching_grants))

        user = req.get('user', '')
        req['try_link_user'] = False
        req['userid'] = None
        if len(user):
            userid = sapi.obtainUserID(user)
            if userid is not None:
                req['try_link_user'] = True
                req['userid'] = userid
            else:
                req['elab_messages'].append('user_not_found')

        doi = req.get('doi', '')
        req['pubid'] = None
        if len(doi):
            pubs = sapi.getListOfPubsQuery('"' + doi + '"')
            pubids = list(pubs.keys())
            pubs_count = len(pubids)
            if pubs_count == 1:
                req['pubid'] = pubids[0]
                req['pub_matched_title'] = pubs[pubids[0]].get('title')
                req['pub_matched_type'] = pubs[pubids[0]].get('type')

            elif pubs_count == 0:
                req['elab_messages'].append('pub_not_found')
            else:
                req['elab_messages'].append('multiple_matching_pubs: ' +
                        ', '.join(pubids))

        # if we can't find the pub, we can't do much anything
        if req['pubid'] == None:
            req['try_link_grant'] = False
            req['try_link_user'] = False

        # check this pub to see if the links might already exist. If so,
        # then nothing to do
        if req['try_link_grant'] or req['try_link_user']:
            existing_rels = sapi.getPubRelationships(req['pubid'])

            if req['try_link_grant']:
                grant_link_exists = sapi.checkRelationshipExists(existing_rels,
                        req['grantid'], pub_rel_grant_type_id)
                if grant_link_exists:
                    req['try_link_grant'] = False
                    req['elab_messages'].append('grant_link_exists')
                else:
                    req['elab_messages'].append('grant_link_does_not_exist')

            if req['try_link_user']:
                user_link_exists = sapi.checkRelationshipExists(existing_rels,
                        req['userid'], pub_rel_author_type_id)
                if user_link_exists:
                    req['try_link_user'] = False
                    req['elab_messages'].append('user_link_exists')
                else:
                    req['elab_messages'].append('user_link_does_not_exist')


def runRequestList(rl, sapi):

    pub_rel_grant_type_id = sapi.findRelationshipTypeID('publication-grant-funded')
    pub_rel_author_type_id = sapi.findRelationshipTypeID('publication-user-authorship')

    if pub_rel_grant_type_id is None:
        print('-err- could not find grant/pub typeid')
        return
    if pub_rel_author_type_id is None:
        print('-err- could not find author/pub typeid')
        return

    for req in rl:

        req['attempt_messages'] = []

        whats = ['user', 'grant']
        for what in whats:

            if req['try_link_' + what]:
                try:
                    payload = {
                        '@xmlns': 'http://www.symplectic.co.uk/publications/api',
                        'from-object': 'publication(' + req['pubid'] + ')',
                    }
                    if what == 'user':
                        payload['to-object'] = 'user(' + req['userid'] + ')'
                        payload['type-id'] = pub_rel_author_type_id
                    elif what == 'grant':
                        payload['to-object'] = 'grant(' + req['grantid'] + ')'
                        payload['type-id'] = pub_rel_grant_type_id

                    req['link_' + what + '_payload'] = payload
                    url = 'relationships'
                    res = sapi.post(url, req['link_' +what + '_payload'], 'import-relationship')
                    err = res['feed']['entry'].get('error')
                    if err is not None:
                        req['attempt_messages'].append(res['feed']['entry']['error']['#text'])
                    req['link_' + what + '_result'] = res
                except Exception as e:
                    req['attempt_message'].append('link_' + what + '_exception: ' + repr(e))



if __name__ == '__main__':
    args = readArgs()

    if 'help' in args or 'infile' not in args:
        print(getHelp())
        sys.exit()

    sapi = sympl_api_highlevel.SymplecticAPI(args)

    print('-info- loading input file: ' + args['infile'])
    reqlist = csvloader.load(args['infile'], args['dialect'])

    print('-info- preparing list of actions from input')
    elaborateRequestList(reqlist, sapi)

    if not args['fake']:
        print('-info- running actions')
        runRequestList(reqlist, sapi)

    print('-info- saving results')
    debughelpers.dumpJS(reqlist, args['jsoutfile'])
    csvloader.dump(reqlist, args['csvoutfile'], None, args['dialect'])

    sapi.saveCache()
