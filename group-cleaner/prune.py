#!/usr/bin/python3
"""
This script reads the data file produced by notify.py and checks if the
users that were notified have hearted the notification post.  Based on
that it removes them from the group as appropriate.

Parameters:
  data_file: The path to the data file generated by notify.py
  for_realz: Really prune people (otherwise don't, just report the results as
    if you would)  
  
Data for a given run is stored under data/<group_id>/<YYMMDDHHMMSS>

Logs are under data/logs 

"""

import argparse
from datetime import datetime
from datetime import timedelta
from glob import glob
import groupy  # https://github.com/rhgrant10/Groupy
import logging
import os
import pickle

parser = argparse.ArgumentParser(description = 'Remove inactive group members')
parser.add_argument('data_file',
                    type=str,
                    help='The data file to be processed')
parser.add_argument('--ya_rly',
                    action='store_true',
                    help='Really prune the group...')

SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))
DATADIR = SCRIPTDIR + '/data'

LOG = logging.getLogger('prune')
LOG.setLevel(logging.DEBUG)

GROUP_REMOVAL_MESSAGE = (
    "I'm going to remove inactive people from the group shortly.  They "
    "have not posted or liked anything in the group for an extended period "
    "and have not responded to my PMs.  They are welcome back at any time."
)

PERSONAL_REMOVAL_MESSAGE = (
    "OK, I haven't seen a response so I'm going to remove you from \'{0}\'. "
    "Feel free to rejoin at any time (speak to a mod)."
)

"""
Given a data file name, return the most recent revision
"""
def selectNewestDataFile(filename):
    print(filename)
    if not os.path.isfile(filename):
        LOG.error('{0} is not a file.'.format(filename))
      
    (head, tail) = os.path.split(filename)
    prefix = tail[:14]
  
    pattern = head + '/' + prefix + '*'
    LOG.debug('Getting all files matching {0}'.format(pattern))
    dir_entries = glob(pattern)
    dir_entries.sort()
  
    LOG.debug("Selecting {0} as the most recent data file version".format(dir_entries[-1]))
    return dir_entries[-1]


"""
Given a data file name return the next revision
"""
def selectNextDataFile(filename):
    (head, tail) = os.path.split(filename)
    prefix = tail[:14]
    if len(tail) > 14:
        suffix = int(tail[15:])
    else:
        suffix = 0
    
    suffix += 1
    
    revison_name = head + '/' + prefix + '.' + str(suffix)
    LOG.debug("Selecting {0} as the next data file version".format(revison_name))
    return revison_name


"""Find the group object given a group ID"""
def findGroupFromID(group_id, group_class = groupy.Group):
    target_group = None
    for g in group_class.list():
        if g.group_id == group_id:
            LOG.info('Found group id {0} "{1}"'.format(g.group_id, g.name))
            target_group = g
            break
    if not target_group:
        LOG.error('Could not find group id {0}'.format(group_id))
        
    return target_group

"""Get the inactive members from member_status"""
def getInactiveMembers(member_status):
    now = datetime.now()
    inactive = []
    
    for id in member_status.keys():
        if member_status[id]['active']:
            continue
        if not member_status[id]['message_id']:
            continue
        if member_status[id]['deadline'] > now:
            continue
        inactive.append(member_status[id]['obj'])


"""Check the pending PMs and update member_status"""
def updateMemberStatusFromPMs(member_status):
    
    for member in getInactiveMembers(member_status):
        status = member_status[member.user_id]
        message_seen = False
        
        messages = m.messages()
        while True:
            
            for message in messages:
                
                if message.created_at < status['message_sent']:
                    break
                
                if message.id == status['message_id']:
                    message_seen = True
                    
                    if member.user_id in message.favorited_by:
                        # This is not entirely accurate, but likes don't have
                        # a timestamp
                        status['lastSeen'] = message.created_at
                        status['active'] = True
                        status['message_id'] = None
                        status['message_sent'] = None
                        
                    break
                
            if message_seen:
                break
            
            if messages[-1].created_at < status['message_sent']:
                break
            
            messages = messages.older()
        

"""Remove inactive members from the group with appropriate notifications"""
def removeInactiveMembers(member_status, group, ya_rly):
    
    LOG.info('Sending a notice to {0}...'.format(group.name))
    if ya_rly:
        group.post(GROUP_REMOVAL_MESSAGE)
    
    for member in getInactiveMembers(member_status):
        LOG.info('Sending a notice to {0}...'.format(member.nickname))
        if ya_rly:
          member.post(PERSONAL_REMOVAL_MESSAGE.format(group.name))
      
        LOG.info('Removing {0} from {1}...'.format(
            member.nickname,
            group.name))
        if ya_rly:
            group.remove(member)

        LOG.debug('Removing {0} from status data.')
        if ya_rly:
            del member_status[member.user_id]
        

"""Get the group given the data file path"""
def getGroupFromDataFilePath(path):
    (head, tail) = os.path.split(path)
    if os.path.islink(head):
        head = os.readlink(head)
    (head, group_id) = os.path.split(head)
    
    group = findGroupFromID(group_id)  
    return group


"""Main program"""
def main(args):
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    LOG.addHandler(ch)    
    
    group = getGroupFromDataFilePath(args.data_file)
    if not group:
        LOG.error('Could not find group ID from file {0}'.format(
            args.data_file))
        sys.exit(0)
    
    filename = selectNewestDataFile(args.data_file)
    
    nextfilename = selectNextDataFile(filename)
    fh = logging.FileHandler(nextfilename + '.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    LOG.addHandler(fh)
    
    with open(filename, 'rb') as f:
        member_status = pickle.load(f)
    
    updateMemberStatusFromPMs(member_status)
    
    # Save updated member status in a new file, named with the same YYYYMMDDHHMMSS
    # as the source file, but with an incremented number at the end.  So if the file
    # we read was 20150504123445 then the new file is 20150504123445.1, and if the
    # source file was .1 then the new file is .2    
    
    with open(nextfilename, 'wb') as f:
        removeInactiveMembers(member_status, group, args.ya_rly)
        pickle.dump(member_status, f)
    
    
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)



