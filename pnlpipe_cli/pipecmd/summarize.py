from __future__ import print_function
from plumbum import cli, local
from pnlpipe_cli import printTable
from ..readparams import read_grouped_combos, make_pipeline
from ..display import printVertical
import sys

class Summarize(cli.Application):
    """Calls a pipeline's summarize function that creates an overall summary report"""
    extraFlags = cli.SwitchAttr(
        ['--extra'], help="Extra flags passed to the pipeline's status function")

    def main(self, *args):
        if args:
            print("Unknown command {0!r}".format(args[0]))
            return 1

        if hasattr(self.parent, 'summarize'):
            if self.extraFlags:
                self.parent.summarize(extraFlags=self.extraFlags.split())
            else:
                self.parent.summarize()
        else:
            print("'pnlpipe_pipelines/{}.py' has no summarize() function.".format(
                self.parent.pipeline_name))
