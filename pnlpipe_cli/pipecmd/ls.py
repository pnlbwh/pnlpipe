from __future__ import print_function
from plumbum import cli, local
from ..display import printVertical
from ..readparams import read_grouped_combos, make_pipeline
from . import ParamApp
import logging
log = logging.getLogger(__name__)
import sys


def print_node_path(nodepath,
                    caseid,
                    print_caseid_only=False,
                    print_csv=False,
                    print_symlink=False):
    if print_caseid_only:
        print('{}'.format(caseid))
        return

    if print_csv:
        sys.stdout.write('{},'.format(p.caseid))
    print(nodepath)


class Ls(ParamApp):
    """List given pipeline file paths."""

    print_csv = cli.Flag(
        ['-c', '--csv'],
        excludes=['-s'],
        help="Print subject ids and paths separated by comma")

    print_caseid_only = cli.Flag(
        ['-s', '--subjid'],
        excludes=['-c'],
        help="Print subject ids instead of paths")

    ignore_caseids = cli.SwitchAttr(
        ['-e', '--except'], default="", help="Ignore this list of caseids")

    print_missing = cli.Flag(
        ['-x', '--missing'],
        default=False,
        excludes=['-a'],
        help="Print missing file paths instead of existing ones")

    print_all = cli.Flag(
        ['-a', '--all'],
        excludes=['-x'],
        default=False,
        help="Print file path whether it exists or not")

    def main(self, *tags):

        ignore_caseids = self.ignore_caseids.split()
        if len(ignore_caseids) == 1 and './' in ignore_caseids[0]:
            ignore_caseids = interpret_caseids(ignore_caseids[0])

        pipeline_name = self.parent.pipeline_name

        grouped_combos = read_grouped_combos(pipeline_name)
        self.validate(len(grouped_combos))

        for paramid, combo, caseids in grouped_combos:

            if self.paramid and paramid != self.paramid:
                continue

            print('', file=sys.stderr)
            print("## Parameter Combination {} ({} cases)".format(
                paramid, len(caseids)), file=sys.stderr)
            printVertical(combo)
            print('', file=sys.stderr)

            for caseid in caseids:
                pipeline = make_pipeline(pipeline_name, combo, caseid)
                for tag in tags:
                    if tag not in pipeline.keys():
                        log.error(
                            "Tag '{}' not defined for pipeline '{}' (Run './pnlpipe {} status' to see list, or look in 'pnlpipe_pipelines/{}.py)".format(
                                tag, pipeline_name, pipeline_name, pipeline_name))
                        sys.exit(1)
                for tag, node in pipeline.items():
                    if tag not in tags:
                        continue
                    if self.print_missing == local.path(node.output()).exists(
                    ) and not self.print_all:
                        continue
                    if self.print_caseid_only:
                        print('{}'.format(caseid))
                        return
                    if self.print_csv:
                        sys.stdout.write('{},'.format(caseid))
                    print(node.output())
