import sys
from plumbum import local
import yaml
import logging
import pnlpipe_lib
import pnlpipe_lib.nodes.nodes

def printVertical(d, prepend='', fd=sys.stderr):
    for k, v in d.items():
        fd.write("{}{:<25} {:<15}".format(prepend, k, v) + '\n')


def printTable(myDict, colList=None):
    """ Pretty print a list of dictionaries (myDict) as a dynamically sized table.
   Original from http://stackoverflow.com/questions/17330139/python-printing-a-dictionary-as-a-horizontal-table-with-headers
   """
    if not colList: colList = sorted(list(myDict[0].keys()) if myDict else [])
    myList = [colList]  # 1st row = header
    for item in myDict:
        myList.append([str(item[col] or '') for col in colList])
    colSize = [max(map(len, col)) for col in zip(*myList)]
    formatStr = ' | '.join(["{{:<{}}}".format(i) for i in colSize])
    myList.insert(1, ['-' * i for i in colSize])  # Seperating line
    for item in myList:
        print(formatStr.format(*item))
