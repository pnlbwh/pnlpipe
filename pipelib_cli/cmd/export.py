from plumbum import cli, local, FG
from pipelib_cli import readAndSetSrcPaths, SRCPATHS
from pipelib_cli.params import readComboPaths
import sys
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO
import csv
import yaml
from collections import OrderedDict
import pipelines as pipelinesDir

PROJECT_YML = 'project.yml'
PROJECT_INFO_YML = 'projectInfo.yml'
PNL_PROJECTS_DB = 'PNL_PROJECTS_DB'

class Export(cli.Application):
    """Makes 'project.yml' from your configured pipeline(s)."""

    force = cli.Flag(['-f', '--force'], default=False, help='force overwrite')

    def main(self, *pipelineNames):

        if not pipelineNames:
            print("List the pipelines for which you want a project.yml file generated.")
            print
            self.help()
            sys.exit(1)

        if local.path(PROJECT_YML).exists() and not self.force:
            msg = "'{}' already exists, to recreate it delete it first or use --force flag.".format(
                PROJECT_YML)
            print(msg)
            sys.exit(1)

        represent_dict_order = lambda self, data: self.represent_mapping('tag:yaml.org,2002:map', data.items())
        yaml.add_representer(OrderedDict, represent_dict_order)

        pipelines = []
        for subprojectyml in (local.cwd // 'project-*yml'):
            with open(subprojectyml, 'r') as f:
                y = yaml.load(f)
            print("Found '{}', adding it to pipelines in '{}'".format(subprojectyml, PROJECT_YML))
            pipelines.append(y)

        if local.path(PROJECT_INFO_YML).exists():
            print(
                "Found '{}', using that to populate the 'projectInfo' field in '{}'".format(
                    PROJECT_INFO_YML, PROJECT_YML))
            with open(PROJECT_INFO_YML, 'r') as f:
                pi = yaml.load(f)
            mandatoryFields = ['grantId', 'description']
            if not set(mandatoryFields) <= set(pi.keys()):
                errmsg = "'{}' is missing one of the required fields: {}".format(
                    PROJECT_INFO_YML, ', '.join(mandatoryFields))
                raise Exception(errmsg)
        else:
            print(
                "Didn't find '{}', using defaults to populate 'projectInfo' field in '{}'".format(
                    PROJECT_INFO_YML, PROJECT_YML))
            pi = {'grandId': ''}
            pi['description'] = ''

        result = {}
        result['projectInfo'] = pi

        srcPaths = readAndSetSrcPaths()
        srcPathsStr = '\n'.join(['{:<8}:  {}'.format(k,v) for k,v in srcPaths.items()])
        result['projectInfo']['description'] = result['projectInfo']['description'] + \
                                               '\n\n\nInput Keys (from {}):\n\n'.format(SRCPATHS) + srcPathsStr

        for pipelineName in pipelineNames:
            paramFile = local.path(pipelineName + '.params')
            pipelineModule = pipelinesDir.importModule(pipelineName)
            pipelineDoc = pipelineModule.makePipeline.__doc__
            if not paramFile.exists():
                raise Exception("Pipeline '{}' not configured, make a '{}.params' file first.".format(pipelineName, pipelineName))
            combos = readComboPaths(pipelineName + '.params')
            for combo in combos:
                pipeline = {}
                pipelineDescription = pipelineDoc
                pipeline['parameters'] = combo['paramCombo']
                if '_description' in pipeline['parameters'].keys():
                    pipeline['description'] = pipelineModule.__file__ + ' docstring: \n' + pipelineDoc + '\n\n' + 'User Comments:\n' + pipeline['parameters']['_description']
                    del pipeline['parameters']['_description']
                pipeline['paths'] = {}
                pipeline['paths']['caselist'] = combo['caseids']
                for pathKey, subjectPaths in combo['paths'].items():
                    s = subjectPaths[0]
                    pipeline['paths'][pathKey] = s.path.relative_to(local.cwd).__str__()
                    pipeline['paths']['caseid'] = s.caseid
                pipelines.append(pipeline)

        result['pipelines'] = pipelines

        with open(PROJECT_YML, 'w') as f:
            yaml.dump(result, f, default_flow_style=False)
        print("Made '{}'".format(PROJECT_YML))
        if not local.path(PROJECT_INFO_YML).exists():
            print("Now customize the 'projectInfo' section and save.")
