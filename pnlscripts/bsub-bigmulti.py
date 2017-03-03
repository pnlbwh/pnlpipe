#!/usr/bin/env python
from plumbum.cmd import bsub
from plumbum import local, cli
from util import logfmt
from os import getpid

import logging
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

class App(cli.Application):
    DESCRIPTION='Start bsub job'
    numcores = cli.SwitchAttr('-n', int, help='number of CPU cores to use', default=8)
    jobname = cli.SwitchAttr('-J', help='job name', default=getpid())

    def main(self, cmd):
        bsub('-J', self.jobname
             ,'-o', self.jobname+"-%J.out"
             ,'-e', self.jobname+"-%J.err"
             ,'-q', "big-multi"
             ,'-n', self.numcores
             ,cmd)

if __name__ == '__main__':
    App.run()
