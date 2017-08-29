from __future__ import print_function
from plumbum import cli, local
from pnlpipe_cli import printTable
from ..readparams import read_grouped_combos, make_pipeline
import pnlpipe_pipelines
from ..display import printVertical
import sys

def _print(s=''):
    print(s, file=sys.stderr)

class Status(cli.Application):
    """Prints information about a pipeline and its progress."""

    def main(self):
        make_pipelineFn = pnlpipe_pipelines.get_make_pipeline(self.parent.pipeline_name)
        print(make_pipelineFn.__doc__ or 'No description.')

        grouped_combos = read_grouped_combos(self.parent.pipeline_name)
        print("There are {} parameter combination(s) defined in '{}'.".format(len(grouped_combos), self.parent.params_file.relative_to(local.cwd)))

        for paramid, combo, caseids in grouped_combos:
            counts = {}
            caseids = caseids or [None]

            _print()
            print("## Parameter Combination {} ({} case(s))".format(
                paramid, len(caseids)), file=sys.stderr)
            _print()
            _print('Parameters:')
            printVertical(dict(combo, caseids=caseids),
                          keys=list(combo.keys()) + ['caseids'])

            pipeline = make_pipeline(self.parent.pipeline_name, combo, caseids[0])
            pathsmap = {'caseid_placeholder': caseids[0]}
            for tag, node in pipeline.items():
                pathsmap[tag] = local.path(node.output()).relative_to(local.cwd)
            _print()
            _print('Paths:')
            printVertical(pathsmap, keys=['caseid_placeholder'] + \
                          [k for k in list(pathsmap.keys()) if k not in ['caseid_placeholder']])

            for caseid in caseids:
                pipeline = make_pipeline(self.parent.pipeline_name, combo, caseid)
                for tag, node in pipeline.items():
                    if local.path(node.output()).exists():
                        counts[tag] = counts.get(tag, 0) + 1
                    else:
                        counts[tag] = counts.get(tag, 0) + 0

            counts['#cases'] = len(caseids)
            print('', file=sys.stderr)
            header = list(counts.keys())
            header.remove('#cases')
            printTable(counts, header + ['#cases'])

        # call pipeline's custom status
        # print('')
        # if hasattr(self.parent, 'status'):
        #     print
        #     if self.extraFlags:
        #         self.parent.status(grouped_combos, extraFlags=self.extraFlags.split())
        #     else:
        #         self.parent.status(grouped_combos)
