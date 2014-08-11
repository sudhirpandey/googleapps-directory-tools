#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pprint
from apiclient.discovery import build
import httplib2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client import tools
import argparse
import simplejson as json

from const import *
from utils import *


def show_resource(resource):
    print "email:              %s" % resource['email']
    print "role:               %s" % resource['role']
    print "type:               %s" % resource['type']

def show_resource_list(resources, verbose):
    if verbose:
        print "etag: %s" % resources['etag']
        print "kind: %s" % resources['kind']
    if resources.has_key('members'):
        for resource in resources['members']:
            if verbose:
                show_resource(resource)
                print ""
            else:
                print "%s %s %s" % (resource['email'], resource['role'], resource['type'])

def main(argv):
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    subparsers = parser.add_subparsers(help='sub command')

    #-------------------------------------------------------------------------
    # LIST
    #-------------------------------------------------------------------------
    parser_list = subparsers.add_parser('list', help='Retrieves list of all members in a group')
    parser_list.add_argument('groupKey', help='group\'s email address, alias or the unique id')
    parser_list.add_argument('--role', choices=['OWNER', 'MANAGER', 'MEMBER'], help='role')
    parser_list.add_argument('-v', '--verbose', action='store_true', help='show all group data')
    parser_list.add_argument('--json', action='store_true', help='output json')
    parser_list.add_argument('--jsonPretty', action='store_true', help='output pretty json')

    #-------------------------------------------------------------------------
    # GET
    #-------------------------------------------------------------------------
    parser_get = subparsers.add_parser('get', help='Retrieves a group member\'s properties')
    parser_get.add_argument('groupKey', help='group\'s email address, alias or the unique id')
    parser_get.add_argument('memberKey', help='member\'s email address')
    parser_get.add_argument('--json', action='store_true', help='output json')
    parser_get.add_argument('--jsonPretty', action='store_true', help='output pretty json')

    #-------------------------------------------------------------------------
    # INSERT
    #-------------------------------------------------------------------------
    parser_insert = subparsers.add_parser('insert', help='Adds a user to the specified group')
    parser_insert.add_argument('groupKey', help='group\'s email address, alias or the unique id')
    parser_insert.add_argument('email', help='member\'s email address')
    parser_insert.add_argument('--role', choices=['OWNER', 'MANAGER', 'MEMBER'],
                               default='MEMBER', help='role of member')
    parser_insert.add_argument('-v', '--verbose', action='store_true',
                               help='show all group data')
    parser_insert.add_argument('--json', action='store_true', help='output json')
    parser_insert.add_argument('--jsonPretty', action='store_true', help='output pretty json')

    #-------------------------------------------------------------------------
    # PATCH
    #-------------------------------------------------------------------------
    parser_patch = subparsers.add_parser('patch', help='Updates the membership properties of a user in the specified group')
    parser_patch.add_argument('groupKey', help='group\'s email address, alias or the unique id')
    parser_patch.add_argument('memberKey', help='member\'s email address')
    parser_patch.add_argument('--role', choices=['OWNER', 'MANAGER', 'MEMBER'], help='role')
    parser_patch.add_argument('-v', '--verbose', action='store_true', help='show all group data')
    parser_patch.add_argument('--json', action='store_true', help='output json')
    parser_patch.add_argument('--jsonPretty', action='store_true', help='output pretty json')

    #-------------------------------------------------------------------------
    # UPDATE
    #-------------------------------------------------------------------------
    parser_update = subparsers.add_parser('update', help='Updates the membership of a user in the specified group')
    parser_update.add_argument('groupKey', help='group\'s email address, alias or the unique id')
    parser_update.add_argument('memberKey', help='member\'s email address')
    parser_update.add_argument('--role', choices=['OWNER', 'MANAGER', 'MEMBER'], help='role')
    parser_update.add_argument('-v', '--verbose', action='store_true',
                               help='show all group data')

    #-------------------------------------------------------------------------
    # DELETE
    #-------------------------------------------------------------------------
    parser_delete = subparsers.add_parser('delete', help='Removes a member from a group')
    parser_delete.add_argument('groupKey', help='group\'s email address, alias or the unique id')
    parser_delete.add_argument('memberKey', help='member\'s email address')

    args = parser.parse_args(argv[1:])

    # Set up a Flow object to be used if we need to authenticate.
    FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
                                   scope=SCOPES,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage(CREDENTIALS_PATH)
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        print 'invalid credentials'
        # Save the credentials in storage to be used in subsequent runs.
        credentials = tools.run_flow(FLOW, storage, args)

    # Create an httplib2.Http object to handle our HTTP requests and authorize it
    # with our good Credentials.
    http = httplib2.Http()
    http = credentials.authorize(http)

    service = build('admin', 'directory_v1', http=http)

    sv = service.members()

    command = argv[1]

    if command == "list":
        members = []
        pageToken = None
        while True:
            params = { 'groupKey': args.groupKey }
            if args.role:
                params['roles'] = args.role
            if pageToken:
                params['pageToken'] = pageToken
            r = sv.list(**params).execute()

            if args.json or args.jsonPretty:
                if r.has_key('members'):
                    for member in r['members']:
                        members.append(member)
            else:
                show_resource_list(r, args.verbose)

            if r.has_key('nextPageToken'):
                pageToken = r['nextPageToken']
            else:
                break

        if args.json or args.jsonPretty:
            if len(members) == 1:
               if args.jsonPretty:
                   print to_pretty_json(members[0])
               elif args.json:
                   print to_json(members[0])
            else:
               if args.jsonPretty:
                   print to_pretty_json(members)
               elif args.json:
                   print to_json(members)
    elif command == "get":
        r = sv.get(groupKey=args.groupKey, memberKey=args.memberKey).execute()
        if args.jsonPretty:
            print to_pretty_json(r)
        elif args.json:
            print to_json(r)
        else:
            show_resource(r)
    elif command == "insert":
        body = { 'email': args.email, 'role': args.role }
        r = sv.insert(groupKey=args.groupKey, body=body).execute()
        if args.verbose:
            if args.jsonPretty:
                print to_pretty_json(r)
            elif args.json:
                print to_json(r)
            else:
                show_resource(r)
    elif command == "patch":
        body = {}
        if args.role:
            body['role'] = args.role
        if len(body) > 0:
            r = sv.patch(groupKey=args.groupKey, memberKey=args.memberKey, body=body).execute()
            if args.verbose:
                if args.jsonPretty:
                    print to_pretty_json(r)
                elif args.json:
                    print to_json(r)
                else:
                    show_resource(r)
    elif command == "update":
        body = {}
        if args.role:
            body['role'] = args.role
        if len(body) > 0:
            r = sv.update(groupKey=args.groupKey, memberKey=args.memberKey, body=body).execute()
            if args.verbose:
                if args.jsonPretty:
                    print to_pretty_json(r)
                elif args.json:
                    print to_json(r)
                else:
                    show_resource(r)
        else:
            print "no update column"
            return
    elif command == "delete":
        r = sv.delete(groupKey=args.groupKey, memberKey=args.memberKey).execute()
    elif command == 'bulkinsert':
        f = open(args.jsonfile, 'r')
        members = json.load(f, 'utf-8')
        for member in members:
            groupKey = member['groupKey']
            del member['groupKey']
            r = sv.insert(groupKey=groupKey, body=member).execute()
            if args.verbose:
                if args.jsonPretty:
                    print to_pretty_json(r)
                elif args.json:
                    print to_json(r)
                else:
                    show_resource(r)


if __name__ == '__main__':
    main(sys.argv)