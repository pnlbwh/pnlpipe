from plumbum import cli, local, FG
from pipelib_cli import readAndSetSrcPaths
from pipelib_cli.params import readComboPaths
import sys
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO
import csv
import yaml
from collections import OrderedDict

PROJECT_YML = 'project.yml'
PROJECT_INFO_YML = 'projectInfo.yml'
PNL_PROJECTS_DB = 'PNL_PROJECTS_DB'


def csvFromDict(d):
    s = ""
    hdr = 'project,grantId,paramId,caselist,param,paramValue'
    row = ','.join(d.values())
    return hdr + '\n' + row


def readProjectInfo():
    with open(PROJECT_YML, 'r') as f:
        return yaml.load(f)


class Publish(cli.Application):
    """Makes project summary file and pushes to central project database."""

    def main(self, *args):
        if args:
            print("Unknown command {0!r}".format(args[0]))
            return 1
        if self.nested_command:
            return


@Publish.subcommand("init")
class Init(cli.Application):
    """Makes 'project.yml'"""

    def main(self):

        if local.path(PROJECT_YML).exists():
            msg = "'{}' already exists, to recreate it delete it first.".format(
                PROJECT_YML)
            print(msg)
            sys.exit(1)

        represent_dict_order = lambda self, data: self.represent_mapping('tag:yaml.org,2002:map', data.items())
        yaml.add_representer(OrderedDict, represent_dict_order)

        if local.path(PROJECT_INFO_YML).exists():
            print(
                "Found '{}', using that to populate the 'projectInfo' field in '{}'".format(
                    PROJECT_INFO_YML, PROJECT_YML))
            with open(PROJECT_INFO_YML, 'r') as f:
                pi = yaml.load(f)
            mandatoryFields = ['projectName', 'grantId', 'description']
            if not set(mandatoryFields) <= set(pi.keys()):
                errmsg = "'{}' is missing one of the required fields: {}".format(
                    PROJECT_INFO_YML, ', '.join(mandatoryFields))
                raise Exception(errmsg)
        else:
            print(
                "Didn't find '{}', using defaults to populate 'projectInfo' field in '{}'".format(
                    PROJECT_INFO_YML, PROJECT_YML))
            pi = {'grandId': ''}
            pi['projectName'] = local.cwd.dirname.__str__()
            pi['description'] = ''

        result = {}
        result['projectInfo'] = pi

        readAndSetSrcPaths()
        combos = readComboPaths(self.parent.parent.paramsFile)

        pipelines = []
        for combo in combos:
            pipeline = {}
            pipeline['parameters'] = combo['paramCombo']
            pipeline['paths'] = {}
            pipeline['paths']['caselist'] = combo['caseids']
            for pathKey, subjectPaths in combo['paths'].items():
                s = subjectPaths[0]
                pipeline['paths'][pathKey] = s.path.__str__()
                pipeline['paths']['caseid'] = s.caseid
            pipelines.append(pipeline)
        result['pipelines'] = pipelines

        with open(PROJECT_YML, 'w') as f:
            yaml.dump(result, f, default_flow_style=False)
        print("Made '{}'".format(PROJECT_YML))
        if not local.path(PROJECT_INFO_YML).exists():
            print("Now customize the 'projectInfo' section and save.".format(
                PROJECT_YML))


@Publish.subcommand("push")
class Push(cli.Application):
    """Copies project.yml to central project database"""

    def readFullName(self):
        return local.cwd.__str__().replace('/', '-')[1:] + '.yml'

    def main(self):
        import os
        from plumbum.cmd import scp

        centralRepo = os.environ.get(PNL_PROJECTS_DB, None)

        if not centralRepo:
            errmsg = "Set '{}' environment variable first.".format(
                PNL_PROJECTS_DB)
            raise Exception(errmsg)

        destName = centralRepo + '/' + self.readFullName()

        print("Copy project.yml to '{}'".format(destName))
        scp['project.yml', destName] & FG
        print("Successfully copied '{}' to '{}'".format('project.yml',
                                                        destName))
