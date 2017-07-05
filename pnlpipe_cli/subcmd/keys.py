from plumbum import cli, local
from pnlpipe_cli.params import readParamCombos
from pnlpipe_cli.params import readComboPaths
from pnlpipe_cli import readAndSetInputKeyPaths


class Keys(cli.Application):
    """Prints pipeline's keys."""

    def main(self):
        readAndSetInputKeyPaths()
        combo = readComboPaths(self.parent.paramsFile)[0]
        for key in combo['paths'].keys():
            print key
