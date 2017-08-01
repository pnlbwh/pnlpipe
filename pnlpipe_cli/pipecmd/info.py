from __future__ import print_function
from plumbum import cli, local
from ..display import printVertical
from ..readparams import read_grouped_combos, make_pipeline
import logging
import sys

def _print(s=''):
    print(s, file=sys.stderr)

class Info(cli.Application):

    param_id = cli.SwitchAttr(
        ['-p', '--paramid'],
        int,
        mandatory=False,
        help="parameter id")


    def main(self, *keys):

        pipeline_name = self.parent.pipeline_name

        for paramid, combo, caseids \
            in read_grouped_combos(pipeline_name):

            _print()
            print("## Parameter Combination {} ({} cases)".format(
                paramid, len(caseids)), file=sys.stderr)

            _print('Parameters:')
            printVertical(combo)
            _print()

            if caseids:
                pipeline = make_pipeline(pipeline_name, combo, caseids[0])
                pathsmap = {'caseid': caseids[0],
                            'caselist': caseids}
            else:
                pipeline = make_pipeline(pipeline_name, combo)
                pathsmap = {}

            for tag, node in pipeline.items():
                pathsmap[tag] = local.path(node.output()).relative_to(local.cwd)

            _print('Paths:')
            printVertical(pathsmap, keys=['caselist', 'caseid'] + \
                          [k for k in pathsmap.keys() if k not in ['caselist', 'caseid']])
