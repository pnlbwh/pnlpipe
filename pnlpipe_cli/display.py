import sys
from plumbum import local
import yaml
import logging
import pnlpipe_lib
import pnlpipe_lib.nodes

def printVertical(d, prepend='', keys=None, fd=sys.stderr):
    if not keys:
        keys = d.keys()
    for k in keys:
        val = d[k] or 'None'
        fd.write("{}{:<25} {:<15}".format(prepend, k, val) + '\n')


def printTable(d, colList=None):
    """ Pretty print a list of dictionaries (myDict) as a dynamically sized table.
   Original from http://stackoverflow.com/questions/17330139/python-printing-a-dictionary-as-a-horizontal-table-with-headers
   """
    myDict = [d]
    if not colList: colList = sorted(list(myDict[0].keys()) if myDict else [])
    myList = [colList]  # 1st row = header
    for item in myDict:
        myList.append([str(item[col] or '') for col in colList])
    colSize = [max(map(len, col)) for col in zip(*myList)]
    formatStr = ' | '.join(["{{:<{}}}".format(i) for i in colSize])
    myList.insert(1, ['-' * i for i in colSize])  # Seperating line
    for item in myList:
        print(formatStr.format(*item))
