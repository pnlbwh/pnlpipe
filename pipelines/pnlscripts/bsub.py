#!/usr/bin/env python
from plumbum.cmd import bsub
from plumbum import local, cli
from util import logfmt
from os import getpid

import logging
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

class App(cli.Application):
    DESCRIPTION='Start bsub job'

    def main(self, *args):
     if args:
        print("Unknown command {0!r}".format(args[0]))
        return 1
     if not self.nested_command:
        print("No command given")
        return 1   # error exit code


@App.subcommand("bm")
class BigMulti(cli.Application):
    numcores = cli.SwitchAttr('-n', int, help='number of CPU cores to use', default=8)
    jobname = cli.SwitchAttr('-J', help='job name', default=getpid().__str__())
    def main(self, cmd):
        bsub('-J', self.jobname
             ,'-o', self.jobname+"-%J.out"
             ,'-e', self.jobname+"-%J.err"
             ,'-q', "big-multi"
             ,'-n', self.numcores
             ,cmd)



if __name__ == '__main__':
    App.run()
