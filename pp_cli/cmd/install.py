from plumbum import local, cli
import pp_cli
from pp_cli import SRCPATHS
import logging
import pp_software


def loadSoftwareModule(name):
    import importlib
    moduleFile = local.path('pp_software') / (name + '.py')
    if not moduleFile.exists():
        raise Exception(
            "{} does not exist, is there a typo (e.g. in the params file?)".format(
                moduleFile))
    return importlib.import_module('pp_software.' + name)


class SoftwareCommand(cli.Application):
    softwareModules = [local.path(m.__file__).stem for m in pp_software.getModules()]
    USAGE = """    %(progname)s [SWITCHES] %(tailargs)s

where softwareModule is one of:
""" + '\n'.join(softwareModules) + '\n'

    ver = cli.SwitchAttr(['-v', '--version'], help='Software version')

    def main(self, softwareModule):
        if not softwareModule:
            logging.info("Missing pp_software module argument, e.g. BRAINSTools")
            return 1
        pp_softwareModule = loadSoftwareModule(softwareModule)
        if self.ver:
            logging.info("Make '{}'".format(pp_softwareModule.getPath(self.ver)))
            pp_softwareModule.make(self.ver)
        else:
            logging.info("Make '{}'".format(pp_softwareModule.getPath()))
            pp_softwareModule.make()
