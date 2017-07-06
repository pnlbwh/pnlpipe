from plumbum import cli, local
from pnlpipe_lib.cli import printVertical
from pnlpipe_lib.cli.params import readComboPaths
from pnlpipe_lib.cli.pipecmd.symlink import toSymlink
import logging

class Missing(cli.Application):
    """Print missing generated output."""

    caseids = cli.Flag(
        ['-s', '--subjid'], help="Print subject ids instead of paths")
    printFull = cli.Flag(['-p'], help="Print full paths instead of symlinks.")

    def main(self, *keys):
        from itertools import cycle
        defaultKeys = [
            a + str(b)
            for a, b in zip(cycle([self.parent.defaultTarget]), range(1, 5))
        ] + [self.parent.defaultTarget]  # assuming max 5 different pipeline parameter combinations (defined in .params file)
        keys = defaultKeys if not keys else keys
        if not keys:
            raise Exception(
                "'DEFAULT_TARGET' not set in 'pnlpipe_pipelines/pipeline_{}.py', so you must provide a key on the command line, e.g. ./pipe std missing fs".format(
                    self.parent.name))

        for comboPaths in readComboPaths(self.parent.paramsFile):
            logging.info("## Parameter Combination {} ({} subjects)".format(
                comboPaths['paramId'], comboPaths['num']))
            printVertical(comboPaths['paramCombo'])

            for k, vs in comboPaths['paths'].iteritems():
                if k not in keys:
                    continue
                missingPaths = [
                    p for p in filter(lambda x: not x.path.exists(), vs)
                ]
                for p in missingPaths:
                    if self.caseids:
                        print('{}'.format(p.caseid))
                    elif self.printFull:
                        print(p.path)
                    else:
                        symlink = toSymlink(p.caseid, self.parent.name, k,
                                            p.path, comboPaths['paramId'])
                        print(symlink)
