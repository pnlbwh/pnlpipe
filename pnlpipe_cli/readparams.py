from plumbum import local, FG, cli
import yaml
import logging
import itertools
from collections import defaultdict
import importlib
import pnlpipe_pipelines
import pnlpipe_config
from pnlpipe_lib import Node

OBSID_KEY = 'caseid'

def _concat(l):
    return l if l == [] else [item for sublist in l for item in sublist]

def params_file(pipeline_name):
    return local.path('pnlpipe_params') / (pipeline_name + '.params')


def _read_param_dicts(ymlfile):
    """Reads in list of parameter dictionaries from parameter yaml file."""

    if not local.path(ymlfile).exists():
        pipeline = ymlfile.name.split('.')[0]
        raise Exception(
            "'{}' doesn't exist, run './pnlpipe {} init' and edit first.".format(
                ymlfile, pipeline))
    with open(ymlfile, 'r') as f:
        yml = yaml.load(f, Loader=yaml.loader.BaseLoader)

    def mapTuple(xs):
        return [tuple(x) if isinstance(x, list) else x for x in xs]

    result = []
    for paramDict in (yml if isinstance(yml, list) else [yml]):
        listValueDict = dict((k, mapTuple(v)) for k, v in paramDict.items())
        # listValueDict['caseid'] = map(str, listValueDict['caseid'])
        result.append(listValueDict)

    logging.debug("Finished reading parameter file '{}':".format(ymlfile))
    return result


def interpret_caseids(paramval):
    if '/' in paramval[0]:
        if not local.path(paramval[0]).exists():
            print("Missing file '{}'. Make this first.".format(paramval[0]))
            import sys
            sys.exit(1)
        with open(paramval[0], 'r') as f:
            return [line.split()[0] for line in f.read().splitlines()
                    if line.strip() and not line.startswith('#')]
    return paramval


def _unique(combos):
    return list({yaml.dump(combo): combo for combo in combos}.values())


def _expand_param_dicts(param_dicts):
    """Expands params file dictionaries into list: [paramComboDict0, paramComboDict1, ...]"""
    all_param_combos = []
    for param_dict in param_dicts:
        if param_dict.get('caseid', None):
            param_dict['caseid'] = sorted(
                interpret_caseids(param_dict['caseid']))
        value_combos = list(itertools.product(*param_dict.values()))
        param_combos = [dict(zip(param_dict.keys(), value_combo))
                        for value_combo in value_combos]
        all_param_combos.extend(param_combos)
    return _unique(all_param_combos)


def _assert_is_node(node, key):
    if not isinstance(node, Node):
        raise Exception(
            "The object at key '{}' is not a Node, are you missing a leading '_'?".format(
                key))


def read_combos(pipeline_name):
    """Reads a pipeline's parameter file and returns its list of unique parameter combinations: [paramComboDict0, paramComboDict1, ...]"""
    return _expand_param_dicts(_read_param_dicts(params_file(pipeline_name)))


def _group_by(combos, exclude_key):
    """Return parameter combinations grouped by all values
    except an observational id along with a list of the obervational
    ids, e.g. [(combo0, caseids0), (combo1, caseids1), ...]."""

    if not combos:
        raise Exception(
            "Trying to group an empty list of parameter combinations.")

    if not exclude_key:
        return [(combo, []) for combo in combos]

    if exclude_key and exclude_key not in combos[0].keys():
        raise Exception("readparams: Key '{}' not in parameters".format(
            exclude_key))

    result = []
    keyfn = lambda d: sorted([str(v) for k, v in d.items() if k != exclude_key])
    combos = sorted(combos, key=keyfn)
    for _, combos in itertools.groupby(combos, key=keyfn):
        combos = list(combos)
        new_combo = {k: v for k, v in combos[0].items() if k != exclude_key}
        excluded_values = [combo[exclude_key] for combo in combos]
        result.append((new_combo, sorted(excluded_values)))

    if not result:
        raise Exception("_group_by has an empty result")

    return result


def read_grouped_combos(pipeline_name,
                        assert_valid_combos=True,
                        exclude_key=OBSID_KEY):
    """Return parameter combinations grouped by all values
    except an observational id along with a list of the obervational
    ids, e.g. [(0, combo0, caseids0), (1, combo1, caseids1), ...]."""

    combos = read_combos(pipeline_name)

    if assert_valid_combos:
        for combo in combos:
            assert_valid_combo(combo, pipeline_name)

    return [(x,y,z) for x,(y,z) in \
            enumerate(_group_by(combos, exclude_key), 1)]


def make_pipeline(pipeline_name, combo, caseid):
    if not isinstance(combo, dict):
        raise TypeError(
            "make_pipeline: expects parameter combination dictionary")
    args = dict(combo, caseid=caseid)
    make_pipelineFn = pnlpipe_pipelines.get_make_pipeline(pipeline_name)
    args = {k: v for k, v in args.items() if not k.startswith('_')}
    pipeline = make_pipelineFn(**args)
    if not pipeline:
        raise Exception(
            "make_pipeline(..) returned None, did you forget to return dictionary in pnlpipe_pipelines/pipeline_{}?".format(
                pipeline_name))
    return pipeline


def readComboPaths(pipeline_name):
    result = []
    make_pipelineFn = pnlpipe_pipelines.get_make_pipeline(pipeline_name)
    # for each parameter values combo (a parameter point without caseid)
    for i, (combo, caseids) in enumerate(read_grouped_combos(pipeline_name)):
        iStr = str(i)
        comboPaths = {'pipelineName': local.path(paramsFile).stem,
                      'paramCombo': paramCombo,
                      'paths': defaultdict(list),
                      'paramId': i,
                      'num': len(caseids),
                      'caseids': caseids}
        for caseid in caseids:
            args = dict(paramCombo, caseid=caseid)
            args = {k: v for k, v in args.items() if not k.startswith('_')}
            subjectPipeline = make_pipelineFn(**args)
            for pipelineKey, node in subjectPipeline.items():
                if pipelineKey.startswith('_'):
                    continue
                _assert_is_node(node, pipelineKey)
                p = SubjectPath(
                    caseid=caseid, pipelineKey=pipelineKey, path=node.output())
                comboPaths['paths'][pipelineKey].append(p)
        result.append(comboPaths)
    return result

def assert_valid_combo(combo, pipeline_name):
    if not '*mandatory*' in combo.values():
        return True
    raise Exception(
        "'{}' has unfilled mandatory values, replace the '*mandatory*' fields first and then rerun the pipeline.".format(
            params_file(pipeline_name)))


def get_software(combo):
    def softname(key):
        if key.endswith('_hash'):
            return key[:-5]
        elif key.endswith('_version'):
            return key[:-8]
        return ''

    return {softname(k): v for k, v in combo.items() if softname(k)}

# def get_software(combos):
#     """combos is a dict or list of dicts"""
#     if isinstance(combos, dict):
#         return _get_software(combos)
#     return set(_concat([_get_software(combo).items() for combo in combos]))
