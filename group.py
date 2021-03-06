#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import codecs
from apiclient.discovery import build
from apiclient import errors
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
    print "name:               %s" % resource['name']
    print "description:        %s" % resource['description']
    print "adminCreated:       %s" % resource['adminCreated']
    if resource.has_key('directMemberCount'):
        print "directMembersCount: %s" % resource['directMembersCount']
    if resource.has_key('nonEditableAliases'):
        for alias in resource['nonEditableAliases']:
            print "nonEditableAliases: %s" % alias

def show_resource_list(resources, verbose):
    if resources.has_key('groups'):
        for resource in resources['groups']:
            if verbose:
                show_resource(resource)
                print ""
            else:
                print resource['email']

def list_group(sv, args):
    groups = []
    pageToken = None
    while True:
        params = { 'domain': args.domain }
        if pageToken:
             params['pageToken'] = pageToken
        r = sv.list(**params).execute()

        if args.jsonPretty or args.json:
            if r.has_key('groups'):
                for group in r['groups']:
                    groups.append(group)
        else:
            show_resource_list(r, args.verbose)

        if r.has_key('nextPageToken'):
            pageToken = r['nextPageToken']
        else:
            break

    if args.jsonPretty:
        if len(groups) == 1:
            print to_pretty_json(groups[0])
        else:
            print to_pretty_json(groups)
    elif args.json:
        if len(groups) == 1:
            print to_json(groups[0])
        else:
            print to_json(groups)

def get_group(sv, args):
    r = sv.get(groupKey=args.groupKey).execute()
    if args.jsonPretty:
        print to_pretty_json(r)
    elif args.json:
        print to_json(r)
    else:
        show_resource(r)

def insert_group(sv, args):
    body = {"email": args.email}
    if args.name:
        body['name'] = args.name.decode('utf-8')
    if args.description:
        body['description'] = args.description.decode('utf-8')
    r = sv.insert(body=body).execute()
    if args.verbose:
        if args.jsonPretty:
            print to_pretty_json(r)
        elif args.json:
            print to_json(r)
        else:
            show_resource(r)

def patch_group(sv, args):
    body = {}
    if args.email:
        body['email'] = args.email
    if args.name:
        body['name'] = args.name.decode('utf-8')
    if args.description:
        body['description'] = args.description.decode('utf-8')
    if len(body) > 0:
        r = sv.update(groupKey=args.groupKey, body=body).execute()
        if args.jsonPretty:
            print to_pretty_json(r)
        elif args.json:
            print to_json(r)
        else:
            show_resource(r)
    else:
        print "no update column"

def delete_group(sv, args):
    r = sv.delete(groupKey=args.groupKey).execute()

def bulk_insert_group(sv, args):
    f = open(args.jsonfile, 'r')
    groups = json.load(f, 'utf-8')
    for group in groups:
      try:  
       r = sv.insert(body=group).execute()
       if args.verbose:
            if args.jsonPretty:
                print to_pretty_json(r)
            elif args.json:
                print to_json(r)
            else:
                show_resource(r)
      except errors.HttpError, e:
         error = json.loads(e.content)
         code = error['error']['code']
         reason = error['error']['errors'][0]['reason']
         if code == 403 and reason  == "forbidden":
          print "%s could not be added because %s" %(group['email'], reason)
         elif code == 409 and reason  == "duplicate":
          print "%s already exists" %(group['email'])
         else:
          print to_pretty_json(error)
          raise

def main():
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    subparsers = parser.add_subparsers(help='sub command')

    #-------------------------------------------------------------------------
    # LIST
    #-------------------------------------------------------------------------
    parser_list = subparsers.add_parser('list', help='Retrieves list of groups in a domain')
    parser_list.add_argument('domain', help='domain name')
    parser_list.add_argument('--userKey', help='userKey query parameter returns all groups for which a user or group has a membership')
    parser_list.add_argument('-v', '--verbose', action='store_true', help='show all group data')
    parser_list.add_argument('--json', action='store_true', help='output in JSON')
    parser_list.add_argument('--jsonPretty', action='store_true', help='output in pretty JSON')
    parser_list.set_defaults(func=list_group)

    #-------------------------------------------------------------------------
    # GET
    #-------------------------------------------------------------------------
    parser_get = subparsers.add_parser('get', help='Retrieves a group\'s properties')
    parser_get.add_argument('groupKey', help='group\'s email address, alias or the unique id')
    parser_get.add_argument('--json', action='store_true', help='output in JSON')
    parser_get.add_argument('--jsonPretty', action='store_true', help='output in pretty JSON')
    parser_get.set_defaults(func=get_group)

    #-------------------------------------------------------------------------
    # INSERT
    #-------------------------------------------------------------------------
    parser_insert = subparsers.add_parser('insert', help='Creates a group')
    parser_insert.add_argument('email', help='group email address')
    parser_insert.add_argument('-n', '--name', help='group name')
    parser_insert.add_argument('-d', '--description', help='group description')
    parser_insert.add_argument('-v', '--verbose', action='store_true', help='show inserted group data')
    parser_insert.add_argument('--json', action='store_true', help='output in JSON')
    parser_insert.add_argument('--jsonPretty', action='store_true', help='output in pretty JSON')
    parser_insert.set_defaults(func=insert_group)

    #-------------------------------------------------------------------------
    # PATCH
    #-------------------------------------------------------------------------
    parser_patch = subparsers.add_parser('patch', help='Updates a group\'s properties')
    parser_patch.add_argument('groupKey', help='group\'s email address, alias or the unique id')
    parser_patch.add_argument('-n', '--name', help='new group name')
    parser_patch.add_argument('-d', '--description', help='new group description')
    parser_patch.add_argument('-e', '--email', help='new group mail address')
    parser_patch.add_argument('--json', action='store_true', help='output in JSON')
    parser_patch.add_argument('--jsonPretty', action='store_true', help='output in pretty JSON')
    parser_patch.set_defaults(func=patch_group)

    #-------------------------------------------------------------------------
    # DELETE
    #-------------------------------------------------------------------------
    parser_delete = subparsers.add_parser('delete', help='Deletes a group')
    parser_delete.add_argument('groupKey', help='group\'s email address, alias or the unique id')
    parser_delete.set_defaults(func=delete_group)

    #-------------------------------------------------------------------------
    # BULKINSERT
    #-------------------------------------------------------------------------
    parser_bi = subparsers.add_parser('bulkinsert', help='bulk insert')
    parser_bi.add_argument('jsonfile')
    parser_bi.add_argument('-v', '--verbose', action='store_true', help='show inserted group data')
    parser_bi.add_argument('--json', action='store_true', help='output in JSON')
    parser_bi.add_argument('--jsonPretty', action='store_true', help='output in pretty JSON')
    parser_bi.set_defaults(func=bulk_insert_group)

    args = parser.parse_args()

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

    sv = service.groups()

    args.func(sv, args)


if __name__ == '__main__':
    sys.stdout = codecs.getwriter('utf_8')(sys.stdout)
    main()
