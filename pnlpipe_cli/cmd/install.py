#!/usr/bin/env python

from plumbum import local, cli
import logging
logger = logging.getLogger(__name__)
import pnlpipe_software


class SoftwareCommand(cli.Application):
    softwareModules = [name for name, _ in pnlpipe_software.modules()]
    USAGE = """    %(progname)s [SWITCHES] %(tailargs)s

where softwareModule is one of:
""" + '\n'.join(softwareModules) + '\n'

    ver = cli.SwitchAttr(['-v', '--version'], help='Software version')

    def main(self, softwareModule):
        if not softwareModule:
            logger.info("Missing pnlpipe_software module argument, e.g. BRAINSTools")
            return 1
        softwareModule = pnlpipe_software.import_module(softwareModule)
        if self.ver:
            logger.info("Make '{}', version: {}".format(softwareModule.__name__, self.ver))
            softwareModule.make(self.ver)
        else:
            logger.info("Make '{}'".format(softwareModule.get_path()))
            softwareModule.make()

if __name__=='__main__':
    SoftwareCommand()
