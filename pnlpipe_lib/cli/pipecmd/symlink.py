from plumbum import cli, local
from pnlpipe_lib.cli import printVertical
from pnlpipe_lib.cli.params import readComboPaths
import logging
import pnlpipe_lib
import sys
import os


def toSymlink(caseid, pipename, key, path, paramId):
    path = local.path(path)
    suffixes = path.suffixes[-2:]
    if not '.nii' in suffixes:
        suffixes = suffixes[-1:]
    return local.path(
        pnlpipe_lib.OUTDIR / caseid /
        (pipename + '_' + key + str(paramId) + ''.join(suffixes)))


def makeSymlink(src, symlink):
    import os
    #os.symlink(os.path.relpath(src, os.path.dirname(symlink)), symlink)
    src.symlink(symlink)
    if '.nhdr' in src.suffixes:
        src.with_suffix('.raw.gz').symlink(symlink.dirname /
                                           src.with_suffix('.raw.gz').name)


class SymLink(cli.Application):
    """Makes simply named symlinks to fully named nodes"""

    def main(self):
        pipename = self.parent.name

        # for symlink in (pnlpipe_lib.OUTDIR // '*/{}_*'.format(pipename)):
        #     symlink.delete()
        from plumbum.cmd import find
        for symlink in find(pnlpipe_lib.OUTDIR, '-type', 'l').split():
            os.unlink(symlink)

        for comboPaths in readComboPaths(self.parent.paramsFile):
            logging.info("# Make symlinks for parameter combination {}".format(
                comboPaths['paramId']))
            printVertical(comboPaths['paramCombo'])

            for key, subjectPaths in comboPaths['paths'].items():
                existingPaths = [
                    p for p in filter(lambda x: x.path.exists(), subjectPaths)
                ]

                for p in existingPaths:
                    symlink = toSymlink(p.caseid, pipename, key, p.path,
                                        comboPaths['paramId'])
                    sys.stdout.write("Make symlink '{}' --> '{}' ".format(
                        symlink, p.path))
                    if symlink.exists():
                        sys.stdout.write('(Already exists, skipping)\n')
                        continue
                    sys.stdout.write('\n')
                    symlink.dirname.mkdir()
                    makeSymlink(p.path, symlink)
