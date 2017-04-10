from plumbum import cli, local
from pipelib_cli import readAndSetSrcPaths, printVertical
from pipelib_cli.params import readComboPaths
import logging
import pipelib
import sys


def toSymlink(caseid, pipename, key, path, paramId):
    path = local.path(path)
    suffixes = path.suffixes[-2:]
    if not '.nii' in suffixes:
        suffixes = suffixes[-1:]
    return local.path(
        pipelib.OUTDIR / caseid /
        (pipename + '_' + key + str(paramId) + ''.join(suffixes)))


def makeRelativeSymlink(src, symlink):
    import os
    #os.symlink(os.path.relpath(src, os.path.dirname(symlink)), symlink)
    #os.symlink(os.path.relpath(src, os.path.dirname(symlink)), symlink)
    src.symlink(symlink)
    if '.nhdr' in src.suffixes:
        src.with_suffix('.raw.gz').symlink(symlink.dirname /
                                           src.with_suffix('.raw.gz').name)


class SymLink(cli.Application):
    """Makes simply named symlinks to fully named nodes"""

    def main(self):
        pipename = self.parent.name
        readAndSetSrcPaths()
        for symlink in (pipelib.OUTDIR // '*/{}_*'.format(self.parent.name)):
            symlink.delete()
        for comboPaths in readComboPaths(self.parent.paramsFile,
                                             self.parent.makePipeline):
            logging.info("# Make symlinks for parameter combination {}".format(
                comboPaths['id']))
            printVertical(comboPaths['paramCombo'])
            for key, subjectPaths in comboPaths['paths'].items():
                existingPaths = [
                    p for p in filter(lambda x: x.path.exists(), subjectPaths)
                ]
                for p in existingPaths:
                    symlink = toSymlink(p.caseid, pipename, key, p.path,
                                        comboPaths['id'])
                    sys.stdout.write("Make symlink '{}' --> '{}' ".format(
                        symlink, p.path))
                    if symlink.exists():
                        sys.stdout.write('(Already exists, skipping)\n')
                        continue
                    sys.stdout.write('\n')
                    symlink.dirname.mkdir()
                    makeRelativeSymlink(p.path, symlink)
