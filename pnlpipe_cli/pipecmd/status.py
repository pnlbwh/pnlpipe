from __future__ import print_function
from plumbum import cli, local
from pnlpipe_cli import printTable
from ..readparams import read_grouped_combos, make_pipeline
from ..display import printVertical
import sys

def stripKeys(dic, strs):
    def strip(s, strs):
        if not strs:
            return s
        else:
            return strip(s.replace(strs[0], ''), strs[1:])

    return {strip(k, strs): v for k, v in dic.items()}


class Status(cli.Application):
    extraFlags = cli.SwitchAttr(
        ['--extra'], help="Extra flags passed to the pipeline's status function")

    def main(self):
        # paramDescrips = [stripKeys(
        #     dict(p['paramCombo']), ['hash_', 'version_']) for p in combos]


        grouped_combos = read_grouped_combos(self.parent.pipeline_name)
        for paramid, combo, caseids in grouped_combos:
            counts = {}

            print('', file=sys.stderr)
            print("## Parameter Combination {} ({} case(s))".format(
                paramid, len(caseids)), file=sys.stderr)
            printVertical(combo)

            for caseid in caseids:
                pipeline = make_pipeline(self.parent.pipeline_name, combo, caseid)
                for tag, node in pipeline.items():
                    if local.path(node.output()).exists():
                        counts[tag] = counts.get(tag, 0) + 1
                    else:
                        counts[tag] = counts.get(tag, 0) + 0

            counts['cases'] = len(caseids)
            print('', file=sys.stderr)
            header = counts.keys()
            header.remove('cases')
            printTable(counts, header + ['cases'])

        # call pipeline's custom status
        print('')
        if hasattr(self.parent, 'status'):
            print
            if self.extraFlags:
                self.parent.status(grouped_combos, extraFlags=self.extraFlags.split())
            else:
                self.parent.status(grouped_combos)
