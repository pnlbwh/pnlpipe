from plumbum import cli, local
from pnlpipe_cli.readparams import read_grouped_combos, make_pipeline
import pnlpipe_config
import pnlpipe_pipelines
import pnlpipe_lib
import sys
import yaml
from collections import OrderedDict

PROJECT_YML = 'pnlproj.yml'
PROJECT_INFO_YML = 'projectInfo.yml'
PNL_PROJECTS_DB = 'PNL_PROJECTS_DB'


class Export(cli.Application):
    """Makes 'pnlproj.yml' from your configured pipeline(s)."""

    force = cli.Flag(['-f', '--force'], default=False, help='force overwrite')

    def main(self, *pipeline_names):

        if not pipeline_names:
            print(
                "List the pipeline names for which you want a {} file generated.".format(
                    PROJECT_YML))
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

        projdicts = []

        for subprojectyml in (local.cwd // 'pnlproj-*yml'):
            with open(subprojectyml, 'r') as f:
                y = yaml.load(f)
            print("Found '{}', adding it to 'pipelines' in '{}'".format(
                subprojectyml, PROJECT_YML))
            projdicts.append(y)

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
            pi = {'grantId': ''}
            pi['description'] = ''

        result = {}
        result['projectInfo'] = pi

        srcPathsStr = '\n'.join(['{:<8}:  {}'.format(k, v)
                                 for k, v in pnlpipe_config.INPUT_KEYS.items()])
        result['projectInfo']['description'] = result['projectInfo']['description'] + \
                                               '\n\n\nInput Keys (from {}):\n\n'.format('pnlpipe_config.py') + srcPathsStr

        for pipeline_name in pipeline_names:
            mod = pnlpipe_pipelines.import_module(pipeline_name)
            doc = mod.make_pipeline.__doc__
            for paramid, combo, caseids in read_grouped_combos(pipeline_name):
                projdict = {}
                projdict['description'] = doc
                projdict['parameters'] = combo
                if '_description' in combo.keys():
                    projdict['description'] = '{} docstring: \n {}\n\nUserComments:\n{}'.format(mod.__file__, doc, projdict['parameters']['_description'])
                    del projdict['parameters']['_description']
                projdict['paths'] = {}
                projdict['paths']['caselist'] = caseids

                pipeline = make_pipeline(pipeline_name, combo, caseids[0])
                projdict['paths']['caseid'] = caseids[0]
                for tag, node in pipeline.items():
                    nodepath = local.path(node.output())
                    projdict['paths'][tag] = nodepath.relative_to(local.cwd).__str__()

                projdicts.append(projdict)

        result['pipelines'] = projdicts

        with open(PROJECT_YML, 'w') as f:
            yaml.dump(result, f, default_flow_style=False)
        print("Made '{}'".format(PROJECT_YML))
        if not local.path(PROJECT_INFO_YML).exists():
            print("Now customize the 'projectInfo' section and save.")
