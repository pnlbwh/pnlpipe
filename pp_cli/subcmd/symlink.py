from plumbum import cli, local
from pp_cli import readAndSetSrcPaths, printVertical
from pp_cli.params import readComboPaths
import logging
import pnlpipe
import sys
import os


def toSymlink(caseid, pipename, key, path, paramId):
    path = local.path(path)
    suffixes = path.suffixes[-2:]
    if not '.nii' in suffixes:
        suffixes = suffixes[-1:]
    return local.path(
        pnlpipe.OUTDIR / caseid /
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
        readAndSetSrcPaths()

        # for symlink in (pnlpipe.OUTDIR // '*/{}_*'.format(pipename)):
        #     symlink.delete()
        from plumbum.cmd import find
        for symlink in find(pnlpipe.OUTDIR, '-type', 'l').split():
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
