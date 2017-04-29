from plumbum import cli, local
from pipelib_cli import readAndSetSrcPaths, printVertical
from pipelib_cli.params import readComboPaths
from pipelib_cli.subcmd.symlink import toSymlink
import logging
import pipelib
import sys


class Ls(cli.Application):
    csv = cli.Flag(
        ['-c', '--csv'],
        excludes=['-s'],
        help="Print subject ids and paths separated by comma")
    caseids = cli.Flag(
        ['-s', '--subjid'],
        excludes=['-c'],
        help="Print subject ids instead of paths")
    printFull = cli.Flag(
        ['-p'], excludes=['-s'], help="Print full paths instead of symlinks.")

    def main(self, *keys):
        readAndSetSrcPaths()
        for comboPaths in readComboPaths(self.parent.paramsFile,
                                             self.parent.makePipeline):
            logging.info("## Parameter Combination {} ({} subjects)".format(
                comboPaths['paramId'], comboPaths['num']))
            printVertical(comboPaths['paramCombo'])
            for k, vs in comboPaths['paths'].iteritems():
                if keys and k not in keys:
                    continue
                existingPaths = [p
                                 for p in filter(lambda x: x.path.exists(), vs)
                                 ]
                for p in existingPaths:
                    if self.caseids:
                        print('{}'.format(p.caseid))
                        continue
                    elif self.csv:
                        sys.stdout.write('{},'.format(p.caseid))
                    if self.printFull:
                        print(p.path)
                    else:
                        symlink = toSymlink(p.caseid, self.parent.name, k,
                                            p.path, comboPaths['id'])
                        print(symlink)
