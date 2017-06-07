from plumbum import local, FG, cli
import yaml
import logging
import itertools
from collections import defaultdict
import importlib
import pipelines


def concat(l):
    return l if l == [] else [item for sublist in l for item in sublist]


def readParamDicts(ymlfile):
    """Reads in list of parameter dictionaries from parameter yaml file."""

    if not local.path(ymlfile).exists():
        pipeline = ymlfile.name.split('.')[1]
        raise Exception(
            "'{}' doesn't exist, run './pipe {} init' first".format(ymlfile,
                                                                    pipeline))
    with open(ymlfile, 'r') as f:
        yml = yaml.load(f)

    def mapTuple(xs):
        return [tuple(x) if isinstance(x, list) else x for x in xs]

    result = []
    for paramDict in (yml if isinstance(yml, list) else [yml]):
        listValueDict = dict((k, mapTuple(v)) for k, v in paramDict.items())
        listValueDict['caseid'] = map(str, listValueDict['caseid'])
        result.append(listValueDict)

    logging.debug("Finished reading parameter file '{}':".format(ymlfile))
    return result


def checkParams(paramDicts):
    if '*mandatory*' in concat([concat(d.values()) for d in paramDicts]):
        raise Exception(
            "First replace '*mandatory*' values in params file and then run again.")


def readCaseids(caseidVal):
    if '/' in caseidVal[0]:
        with open(caseidVal[0], 'r') as f:
            return [line.split()[0] for line in f.read().splitlines()
                    if not line.startswith('#')]
    return caseidVal


def expandParamDicts(paramsDicts):
    """Returns [(paramCombo0, caseids0), (paramCombo1, caseids1), ...]"""
    parametersList = []
    for paramsDict in paramsDicts:
        caseids = sorted(readCaseids(paramsDict['caseid']))
        paramsNoCaseid = paramsDict
        del paramsNoCaseid['caseid']
        valueCombos = list(itertools.product(*paramsNoCaseid.values()))
        paramCombos = [dict(zip(paramsNoCaseid.keys(), valueCombo))
                       for valueCombo in valueCombos]
        parametersList.append(
            [(paramCombo, caseids) for paramCombo in paramCombos])
    unique = lambda xs: list({yaml.dump(x): x for x in xs}.values())
    return unique(concat(parametersList))


from collections import namedtuple
SubjectPath = namedtuple('SubjectPath', 'caseid pipelineKey path')


def assertIsNode(node, key):
    if not node or not hasattr(node, 'build') or not hasattr(node, 'path'):
        raise Exception(
            "The object at key '{}' is not a Node, are you missing a leading '_'?".format(
                key))


def readParamCombos(paramsFile):
    return expandParamDicts(readParamDicts(paramsFile))


def readComboPaths(paramsFile):
    result = []
    pipelineName = local.path(paramsFile).stem
    pipelineModule = pipelines.importModule(pipelineName)
    # for each parameter values combo (a parameter point without caseid)
    for i, (paramCombo, caseids) in enumerate(readParamCombos(paramsFile)):
        iStr = str(i)
        comboPaths = {'pipelineName': local.path(paramsFile).stem,
                         'paramCombo': paramCombo,
                         'paths': defaultdict(list),
                         'paramId': i,
                         'num': len(caseids),
                         'caseids': caseids}
        for caseid in caseids:
            args = dict(paramCombo, caseid=caseid)
            args = {k:v for k,v in args.items() if not k.startswith('_')}
            subjectPipeline = pipelineModule.makePipeline(**args)
            for pipelineKey, node in subjectPipeline.items():
                if pipelineKey.startswith('_'):
                    continue
                assertIsNode(node, pipelineKey)
                p = SubjectPath(
                    caseid=caseid, pipelineKey=pipelineKey, path=node.path())
                comboPaths['paths'][pipelineKey].append(p)
        result.append(comboPaths)
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
