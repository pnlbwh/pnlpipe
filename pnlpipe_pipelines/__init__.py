import importlib
from os.path import isfile
import pkgutil

def modules():
    """Returns (pipelineName, pipelineModule)"""

    for importer, modname, ispkg in pkgutil.iter_modules(__path__):
        if not modname.startswith('_'):
            m = importer.find_module(modname).load_module(modname)
            # name = modname[:-9]
            name = modname
            yield name, m


def import_module(name):
    pipelineModuleName = name #+ '_pipeline'
    try:
        return importlib.import_module('pnlpipe_pipelines.' + pipelineModuleName)
    except:
        raise Exception("Cannot import '{}'".format(pipelineModuleName))

def module_file(name):
    return 'pnlpipe_pipelines/{}.py'.format(name)


def get_make_pipeline(name):
    m = import_module(name)
    if hasattr(m, 'make_pipeline'):
        return m.make_pipeline
    raise Exception("'{}' is missing its 'make_pipeline' function".format(module_file(name)))


def default_target(name):
    m = import_module(name)
    result = getattr(m, 'DEFAULT_TARGET', None)
    if result:
        return result
    raise Exception("{}: 'DEFAULT_TARGET' not set in {}, don't know what to build".format(m.__file__))
