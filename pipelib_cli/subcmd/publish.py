from plumbum import cli, local
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

PUBLISH_CONFIG_FILE = 'publish.yml'
PNLPROJECTSMETA = 'PNLPROJECTSMETA'

def csvFromDict(d):
    s = ""
    hdr = 'project,projectPath,grantId,paramId,caselist,param,paramValue'
    row = ','.join(d.values())
    return hdr + '\n' + row


def readProjectInfo():
    with open(PUBLISH_CONFIG_FILE, 'r') as f:
        return yaml.load(f)

class Publish(cli.Application):

    def main(self, *args):
        if args:
            print("Unknown command {0!r}".format(args[0]))
            return 1
        if self.nested_command:
            return

        readAndSetSrcPaths()
        combos = readComboPaths(self.parent.paramsFile)
        projectInfo = readProjectInfo()

        paramsCsv = '_{}_publish_params.csv'.format(self.parent.name)
        pathsCsv = '_{}_publish_paths.csv'.format(self.parent.name)

        with open(paramsCsv, 'w') as fparamsCsv:
            csvwriter = csv.writer(fparamsCsv)
            hdr = ['project', 'projectPath', 'description', 'paramId'
                ,'param', 'paramValue']
            csvwriter.writerow(hdr)
            with open(pathsCsv, 'w') as fpathsCsv:
                hdr = ['project', 'projectPath', 'paramId', 'pathKey', 'caseid',
                        'path', 'exists']
                csvwriter2 = csv.writer(fpathsCsv)
                csvwriter2.writerow(hdr)

                for combo in combos:
                    for k, v in combo['paramCombo'].items():
                        csvwriter.writerow([projectInfo['project'],
                                            projectInfo['projectPath'],
                                            projectInfo['description'], combo['paramId'], k,
                                            v])
                    for pathKey, subjectPaths in combo['paths'].items():
                        for subjectPath in subjectPaths:
                            csvwriter2.writerow(
                                [projectInfo['project'], projectInfo['projectPath'],
                                combo['paramId'], pathKey, subjectPath.caseid,
                                subjectPath.path, subjectPath.path.exists()])
            print("Made '{}'".format(paramsCsv))
            print("Made '{}'".format(pathsCsv))


@Publish.subcommand("init")
class Init(cli.Application):
    def main(self):
        represent_dict_order = lambda self, data: self.represent_mapping('tag:yaml.org,2002:map', data.items())
        yaml.add_representer(OrderedDict, represent_dict_order)

        with open(PUBLISH_CONFIG_FILE, 'w') as f:
            f.write('project: {}\n'.format(local.cwd.dirname.__str__()))
            f.write('projectPath: {}\n'.format(local.cwd.__str__()))
            f.write('grantId: {}\n'.format(''))
            f.write('description: {}\n'.format(''))


        print("Made '{}'".format(PUBLISH_CONFIG_FILE))


@Publish.subcommand("push")
class Push(cli.Application):

    def main(self):
        import os
        centralRepo = os.environ.get(PNLPROJECTSMETA, None)
        if not centralRepo:
            errmsg = "Set '{}' environment variable first.".format(PNLPROJECTSMETA)
            raise Exception(errmsg)

        paramsCsv = local.path('_{}_publish_params.csv'.format(self.parent.parent.name))
        pathsCsv = local.path('_{}_publish_paths.csv'.format(self.parent.parent.name))

        if not paramsCsv.exists():
            errmsg = "'{}' does not exist, run 'publish' command first".format(paramsCsv)
            raise Exception(errmsg)
        if not pathsCsv.exists():
            errmsg = "'{}' does not exist, run 'publish' command first".format(pathsCsv)
            raise Exception(errmsg)
