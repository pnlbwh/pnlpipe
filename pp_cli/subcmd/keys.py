from plumbum import cli, local
from pp_cli.params import readParamCombos
from pp_cli.params import readComboPaths
from pp_cli import readAndSetSrcPaths


class Keys(cli.Application):
    """Prints pipeline's keys."""

    def main(self):
        readAndSetSrcPaths()
        combo = readComboPaths(self.parent.paramsFile)[0]
        for key in combo['paths'].keys():
            print key
