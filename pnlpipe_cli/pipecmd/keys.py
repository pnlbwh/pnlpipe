from plumbum import cli, local
from pnlpipe_cli.readparams import read_combos, make_pipeline


class Keys(cli.Application):
    """Prints pipeline's keys."""

    def main(self):
        combo = read_combos(self.parent.pipeline_name)[0]
        pipeline = make_pipeline(self.parent.pipeline_name, combo)
        for key in pipeline.keys():
            print key
