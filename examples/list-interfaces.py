#!/usr/bin/snimpy

load("IF-MIB")
m=M()

for i in m.ifDescr:
    print "Interface %3d:   %s" % (i, m.ifDescr[i])
