#! /usr/bin/env python
import re

heading = 'UNIT      LOAD      ACTIVE   SUB       DESCRIPTION'
row     = 'unit      load      active   sub       description'
column_title = 'LOAD'
match = re.search(re.compile(column_title + '\s+'), heading)

print(match.start())
print(match.end())
