from plumbum import local, cli
import pipelib_cli
from pipelib_cli import SRCPATHS
import logging


def loadSoftwareModule(name):
    import importlib
    moduleFile = local.path('software') / (name + '.py')
    if not moduleFile.exists():
        raise Exception(
            "{} does not exist, is there a typo (e.g. in the params file?)".format(
                moduleFile))
    return importlib.import_module('software.' + name)


class SoftwareCommand(cli.Application):
    ver = cli.SwitchAttr(['-v', '--version'], help='Software version')

    def main(self, softname):
        if not softname:
            logging.info("Missing software module argument, e.g. BRAINSTools")
            return 1
        softwareModule = loadSoftwareModule(softname)
        if self.ver:
            logging.info("Make '{}'".format(softwareModule.getPath(self.ver)))
            softwareModule.make(self.ver)
        else:
            logging.info("Make '{}'".format(softwareModule.getPath()))
            softwareModule.make()
