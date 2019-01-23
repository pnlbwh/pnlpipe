from __future__ import print_function
from plumbum import cli, local
from pnlpipe_cli import printTable
from ..readparams import read_grouped_combos, make_pipeline
from ..display import printVertical
import sys

class Summarize(cli.Application):
    """Calls a pipeline's summarize function that creates an overall summary report"""
    extra_flags = cli.SwitchAttr(
        ['--extra', '-e'], help="Extra flags passed to the pipeline's summarize function")

    def main(self, *args):
        if args:
            print("Unknown command {0!r}".format(args[0]))
            return 1

        if hasattr(self.parent, 'summarize'):
            if self.extra_flags:
                self.parent.summarize(self.extra_flags.split())
            else:
                self.parent.summarize()
        else:
            print("'pnlpipe_pipelines/{}.py' has no summarize() function.".format(
                self.parent.pipeline_name))
