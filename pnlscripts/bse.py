#!/usr/bin/env python

from __future__ import print_function
import operator
from util import logfmt, ExistingNrrd
from plumbum import local, cli, FG
from plumbum.cmd import unu

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))


def get_grad_dirs(hdr):
    return [map(float, line.split(b'=')[1].split())
            for line in hdr.splitlines() if b'DWMRI_gradient' in line]


def get_bval(hdr):
    for line in hdr.splitlines():
        if b'b-value' in line:
            return float(line.split(b'=')[1])


def get_b0_index(hdr):
    bval = get_bval(hdr)
    bvals = [norm(gdir) * bval for gdir in get_grad_dirs(hdr)]
    idx, min_bval = min(enumerate(bvals), key=operator.itemgetter(1))
    logger.info("Found B0 of " + str(min_bval) + " at index " + str(idx))
    return idx


def norm(vector):
    return sum([v**2 for v in vector])


class App(cli.Application):
    """Extracts the baseline (b0) from a nrrd DWI.  Assumes
the diffusion volumes are indexed by the last axis."""

    dwimask = cli.SwitchAttr(
        ['-m', '--mask'], ExistingNrrd, help='DWI mask', mandatory=False)
    dwi = cli.SwitchAttr(
        ['-i', '--infile'],
        ExistingNrrd,
        help='DWI nrrd image',
        mandatory=True)
    out = cli.SwitchAttr(
        ['-o', '--out'], help='Extracted B0 nrrd image', mandatory=True)

    def main(self):
        hdr = unu("head", self.dwi)[:-1]
        idx = get_b0_index(hdr)

        slicecmd = unu["slice", "-a", "3", "-p", str(idx), "-i", self.dwi]
        gzipcmd = unu["save", "-e", "gzip", "-f", "nrrd", "-o", self.out]
        if self.dwimask:
            maskcmd = unu["3op", "ifelse", "-w", "1", self.dwimask, "-", "0"]
            (slicecmd | maskcmd | gzipcmd) & FG
        else:
            (slicecmd | gzipcmd) & FG


if __name__ == '__main__':
    App.run()
