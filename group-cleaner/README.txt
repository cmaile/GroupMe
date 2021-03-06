This set of scripts helps manage the population of your 
GroupMe group; ensuring that group members are active
and still interested in being members.

You'll need a real GroupMe account for these.  It can be a
personal account, or a role account created for the occasion.

These scripts use GroupyAPI (http://groupy.readthedocs.org/),
whiuch depends on Python 3.  On my Ubuntu 14.04 I had to
install Python 3, the headers (one of Groupy's dependencies
is in C), and some support tools before I could install using
pip as per the install docs.

You'll need to store your API key in ~/.groupy.key as well.

The scripts:

list-groups.py and list-members.py

These list the groups and members you have seen, respectively.
This is how you can get the IDs for the other scripts.

notify.py

e.g. notify.py <group_id> --ya_rly

This is used to send notifications to members.  It
will:

1) Enumerate all current members
2) Ignore members who have been active in the group in
   the past n days (default 14 days).  
3) Send a PM to all others asking if they are still
   intersted in being in the group
4) Write out a data file (for use by subsequent scripts)
   recording which of these it did to which accounts.
   This will be in data/<group_id>/<datetime> 
   with a symlink data/<group_name> for convenience.
   This is a binary file generated with python's pickle
   module.
5) Log all this in data/<group_id>/<datetime>.log

If you omit the --ya_rly it'll just tell you what it would
do, but won't PM anyone.

prune.py

e.g. prune.py data/<group_id|group_name>/YYMMDDHHMMSS --ya_rly

This is used to prune inactive members.  It depends
on the data file generated by notify.py.

It will:

1) Use the output of notify.py (or most recent sunsequent run of
   itself) to determine which members were PMed and whose reply
   deadlines have passed.
2) Check the response to the PMs - if the person hearted
   the message then they stay in, otherwise they do not.
3) PM the people who will be removed, telling them why.
4) PM the group telling whem why people are being removed.
5) Remove the people from the group.
6) Save the new group data in data/<group_id>/<datetime>.#
6) Log all this in data/<group_id>/<datetime>.#.log

As with notify.py, omit --ya_rly to do a dry run.

migrate_group.py

A script to find all active group members and move them to a
new group.  See --help for details.  
