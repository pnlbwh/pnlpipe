from plumbum import local, FG, cli
import yaml
import logging
import itertools


def concat(l):
    return l if l == [] else [item for sublist in l for item in sublist]


def readParams(ymlfile):
    if not local.path(ymlfile).exists():
        pipeline = ymlfile.name.split('.')[1]
        raise Exception(
            "'{}' doesn't exist, run './pipe {} init' first".format(ymlfile,
                                                                    pipeline))
    with open(ymlfile, 'r') as f:
        yml = yaml.load(f)
    result = []
    for paramDict in (yml if isinstance(yml, list) else [yml]):
        listValueDict = dict((k, v) if isinstance(v, list) else (k, [v])
                             for k, v in paramDict.items())
        listValueDict['caseid'] = map(str, listValueDict['caseid'])
        result.append(listValueDict)
    logging.debug("Finished reading parameter file '{}':".format(ymlfile))
    return result


def checkParams(paramDicts):
    if '*mandatory*' in concat([concat(d.values()) for d in paramDicts]):
        raise Exception(
            "First replace '*mandatory*' values in params file and then run again.")


def readCaseid(caseidVal):
    if '/' in caseidVal[0]:
        with open(caseidVal[0], 'r') as f:
            return [line for line in f.read().splitlines()
                    if not line.startswith('#')]
    return caseidVal


def expandParamCombos(paramsDicts):
    """Returns [(paramCombo, caseids), ...]"""
    parametersList = []
    for paramsDict in paramsDicts:
        caseids = sorted(readCaseid(paramsDict['caseid']))
        paramsNoCaseid = paramsDict
        del paramsNoCaseid['caseid']
        valueCombos = list(itertools.product(*paramsNoCaseid.values()))
        paramCombos = [dict(zip(paramsNoCaseid.keys(), valueCombo))
                       for valueCombo in valueCombos]
        parametersList.append(
            [(paramCombo, caseids) for paramCombo in paramCombos])
    # return list of unique parameters
    return list({yaml.dump(p): p for p in concat(parametersList)}.values())

# def groupDicts(dicts, keyfn):
#     from itertools import groupby
#     return [(k, list(g)) for k, g in groupby(sorted(dicts, key=keyfn), keyfn)]

# def groupParamPointsByCombo(paramsFile):
#     readAndSetInputPaths()
#     paramDicts = readParams(paramsFile)
#     checkParams(paramDicts)
#     pipelineArguments = paramCombos(paramDicts)
#     parameters = groupDicts(pipelineArguments, lambda x: {k:v for k,v in x.items() if k != 'caseid'} )
#     # Sort by parameter points that have most caseids. This is an edge
#     # case, usually there will only be one parameter point, or if more than
#     # one they will be the same length. But, there is a use case when
#     # running a smaller test set to see the effect of a change in one of
#     # the parameters, e.g. a different software version
#     return sorted(parameters, key=lambda x: -len(x[1]))

from collections import namedtuple
SubjectPath = namedtuple('SubjectPath', 'caseid pipelineKey path')


def assertIsNode(node, key):
    if not hasattr(node, 'build') or not hasattr(node, 'path'):
        raise Exception(
            "The object at key '{}' is not a Node, are you missing a leading '_'?".format(
                key))


def readParamCombos(paramsFile):
    return expandParamCombos(readParams(paramsFile))


def readComboPaths(paramsFile, makePipelineFn):
    paramCombos = readParamCombos(paramsFile)
    result = []
    # for each parameter values combo (a parameter point without caseid)
    for i, (paramCombo, caseids) in enumerate(paramCombos):
        iStr = str(i)
        paramComboPaths = {'paramCombo': paramCombo,
                           'paths': [],
                           'id': i,
                           'num': len(caseids)}
        for caseid in caseids:
            args = dict(paramCombo, caseid=caseid)
            subjectPipeline = makePipelineFn(**args)
            for pipelineKey, node in subjectPipeline.items():
                if pipelineKey.startswith('_'):
                    continue
                assertIsNode(node, pipelineKey)
                p = SubjectPath(
                    caseid=caseid, pipelineKey=pipelineKey, path=node.path())
                paramComboPaths['paths'].append(p)
        result.append(paramComboPaths)
    return result


def assertValidParamCombos(paramCombos, paramsFile):
    for paramCombo, _ in paramCombos:
        if '*mandatory*' in paramCombo.values():
            raise Exception(
                "'{}' has unfilled mandatory values, replace the '*mandatory*' fields first and then rerun the pipeline.".format(
                    paramsFile))


def softNameFromKey(paramKey):
    softname = ''
    if paramKey.startswith('hash_'):
        softname = paramKey[5:]
    elif paramKey.startswith('version_'):
        softname = paramKey[8:]
    return softname


def getSoftwareItems(d):
    for k, v in (d.items() if isinstance(d, dict) else d):
        softname = softNameFromKey(k)
        if softname:
            yield softname, v, local.path('software/{}.py'.format(softname))
