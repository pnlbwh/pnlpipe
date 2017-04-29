import importlib

def importModule(name):
    pipelineModuleName = 'pipeline_' + name
    try:
        return importlib.import_module('pipelines.' + pipelineModuleName)
    except:
        raise Exception("Cannot import '{}'".format(pipelineModuleName))
