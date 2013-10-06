#!/usr/bin/snimpy

from __future__ import print_function

load("IF-MIB")
m=M()

for i in m.ifDescr:
    print("Interface %3d:   %s" % (i, m.ifDescr[i]))
