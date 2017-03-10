#!/usr/bin/env python
from __future__ import print_function
from util import logfmt, TemporaryDirectory, ExistingNrrd, NonexistentNrrd
from util.antspath import WarpImageMultiTransform
from plumbum import local, cli, FG
from plumbum.cmd import unu
import re

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


class App(cli.Application):
    """Applies a transformation to a DWI nrrd, with option of masking first.
    (Used by epi.py)"""

    debug = cli.Flag(
        ['-d', '--debug'], help='debug, makes antsApplyTransformsDWi-<pid>')
    dwi = cli.SwitchAttr(
        ['-i', '--infile'], ExistingNrrd, help='DWI', mandatory=True)
    dwimask = cli.SwitchAttr(
        ['--dwimask', '-m'], ExistingNrrd, help='DWI mask', mandatory=False)
    xfm = cli.SwitchAttr(
        ['--transform', '-t'],
        cli.ExistingFile,
        help='transform',
        mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'], NonexistentNrrd, help='Transformed DWI')

    def main(self):
        with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
            tmpdir = local.path(tmpdir)
            dicePrefix = 'dwi'

            logging.info("Dice DWI")
            (unu['convert', '-t', 'int16', '-i', self.dwi] | \
                unu['dice','-a','3','-o',dicePrefix]) & FG

            logging.info("Apply warp to each DWI volume")
            vols = sorted(tmpdir // (dicePrefix + '*'))
            volsWarped = []
            for vol in vols:
                if self.dwimask:
                    unu('3op','ifelse',self.dwimask,vol,'0','-o',vol)
                volwarped = vol.stem + '-warped.nrrd'
                WarpImageMultiTransform('3', vol, volwarped, '-R', vol,
                                        self.xfm)
                unu('convert', '-t', 'int16', '-i', volwarped, '-o', volwarped)
                volsWarped.append(volwarped)

            logging.info("Join warped volumes together")
            (unu['join', '-a', '3', '-i', volsWarped] | \
                unu['save', '-e', 'gzip', '-f', 'nrrd'] | \
                unu['data','-'] > 'tmpdwi.raw.gz') & FG

            logging.info(
                "Create new nrrd header pointing to the newly generated data file")
            unu('save', '-e', 'gzip', '-f', 'nrrd', '-i', self.dwi, '-o',
                'dwi.nhdr')
            with open("dwi.nhdr", "r") as hdr:
                lines = hdr.readlines()
            with open("dwi.nhdr", "w") as hdr:
                for line in lines:
                    hdr.write(
                        re.sub(r'^data file:.*$', 'data file: tmpdwi.raw.gz',
                               line))

            logging.info('Make ' + str(self.out))
            unu('save', '-e', 'gzip', '-f', 'nrrd', '-i', 'dwi.nhdr', '-o',
                self.out)
            logging.info('Made ' + str(self.out))

            if self.debug:
                from os import getpid
                pid = str(getpid())
                d = local.path(self.out.dirname /
                               ('antsApplyTransformsDWi-' + pid))
                tmpdir.copy(d)


if __name__ == '__main__':
    App.run()
