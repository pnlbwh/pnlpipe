from plumbum import local, cli
import pnlpipe_cli
from pnlpipe_cli import SRCPATHS
import logging
import pnlpipe_software


def loadSoftwareModule(name):
    import importlib
    moduleFile = local.path('pnlpipe_software') / (name + '.py')
    if not moduleFile.exists():
        raise Exception(
            "{} does not exist, is there a typo (e.g. in the params file?)".format(
                moduleFile))
    return importlib.import_module('pnlpipe_software.' + name)


class SoftwareCommand(cli.Application):
    softwareModules = [local.path(m.__file__).stem for m in pnlpipe_software.getModules()]
    USAGE = """    %(progname)s [SWITCHES] %(tailargs)s

where softwareModule is one of:
""" + '\n'.join(softwareModules) + '\n'

    ver = cli.SwitchAttr(['-v', '--version'], help='Software version')

    def main(self, softwareModule):
        if not softwareModule:
            logging.info("Missing pnlpipe_software module argument, e.g. BRAINSTools")
            return 1
        pnlpipe_softwareModule = loadSoftwareModule(softwareModule)
        if self.ver:
            logging.info("Make '{}'".format(pnlpipe_softwareModule.getPath(self.ver)))
            pnlpipe_softwareModule.make(self.ver)
        else:
            logging.info("Make '{}'".format(pnlpipe_softwareModule.getPath()))
            pnlpipe_softwareModule.make()
