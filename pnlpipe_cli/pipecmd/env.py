from __future__ import print_function
import sys
from plumbum import cli, local
from ..display import printVertical
from ..readparams import read_grouped_combos, make_pipeline, get_software
import pnlpipe_software
from . import ParamApp

def _print(s=''):
    print(s, file=sys.stderr)

def _escape_path(filepath):
    return filepath.__str__().replace('(', '\(').replace(')', '\)')


class Env(ParamApp):
    """Print bash environment setup (load by running eval `pnlpipe <pipeline> env`). """

    def main(self):

        if not self.paramid:
            self.paramid = 1

        grouped_combos = read_grouped_combos(self.parent.pipeline_name)

        for paramid, combo, caseids in grouped_combos:
            if paramid != self.paramid:
                continue

            pipeline = make_pipeline(self.parent.pipeline_name, combo, caseids[0])

            _print("# Shell environment setup for pipeline {} (out of {})".format(
                paramid, len(grouped_combos)))

            _print("Parameters:")
            printVertical(combo, prepend='#  ')

            for tag, node in pipeline.items():
                nodepath = _escape_path(node.output())
                print('export {}={}\n\n'.format(tag, nodepath))

            print('export {}={}\n\n'.format('caseid', caseids[0]))

            # Software environment
            env_dicts = []
            for softname, version in get_software(combo).items():
                software_module = pnlpipe_software.import_module(softname)
                if hasattr(software_module, 'env_dict'):
                    env_dicts.append(software_module.env_dict(version))
            softVars = pnlpipe_software.composeEnvDicts(env_dicts)
            for var, val in softVars.items():
                print('export {}={}\n\n'.format(var, val))

            print("export PATH={}:$PATH\n".format(local.path('pnlscripts')))
