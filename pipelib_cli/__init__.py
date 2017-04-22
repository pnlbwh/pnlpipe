import sys
import pipelib
from plumbum import local
import yaml
import logging

SRCPATHS = "srcpaths.yml"

def readAndSetSrcPaths():
    if not local.path(SRCPATHS).exists():
        raise Exception(
            "Missing {}, cannot set Src paths".format(SRCPATHS))
    with open(SRCPATHS, 'r') as f:
        inputPathDict = yaml.load(f)
    pipelib.INPUT_PATHS = {}
    caseidPattern = inputPathDict.get('caseid', '{case}').__str__()
    for key, val in inputPathDict.items():
        if not '/' in val:
            continue
        pipelib.INPUT_PATHS[key] = local.path(
            val.replace(caseidPattern, '{case}'))
    logging.debug("Read '{}' and set pipelib.INPUT_PATHS:".format(
        SRCPATHS))


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
