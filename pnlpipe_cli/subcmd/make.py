from plumbum import local, cli
import pnlpipe_cli
from pnlpipe_cli import SRCPATHS, readAndSetInputKeyPaths, printVertical
from pnlpipe_cli.params import readParamCombos, readComboPaths, getSoftwareItems
import importlib
import logging
import pnlpipe_software


class Make(cli.Application):
    """ Builds necessary pnlpipe_software for pipeline and creates shell environment files. """

    fullPaths = cli.Flag(
        ['-p'],
        help="Use full path filenames (containing escaped characters) in the shell environment files instead of shortened symlinks")

    def main(self):
        if not self.parent.paramsFile.exists():
            raise Exception(
                "'{}' doesn't exist, make it first with './pipe {} init'".format(
                    self.parent.paramsFile, self.parent.__class__.__name__))

        logging.info("Build prerequisite pnlpipe_software")
        for (paramCombo, _) in readParamCombos(self.parent.paramsFile):
            for softname, commit, modulefile in getSoftwareItems(paramCombo):
                if not modulefile.exists():
                    raise Exception("{} does not exist".format(modulefile))
                module = importlib.import_module('pnlpipe_software.' + softname)
                logging.info("Make {}".format(module.getPath(commit)))
                module.make(commit)

        logging.info("Make shell environment files")
        makeEnvFiles(self.parent.name, self.parent.paramsFile, self.fullPaths)


def escapePath(filepath):
    return filepath.__str__().replace('(', '\(').replace(')', '\)')


def makeEnvFiles(name, paramsFile, useFullPaths=False):
    # first delete existing files in case they are stale
    for f in local.cwd.glob(name + '*.sh'):
        f.delete()
    # with open('outputPaths.yml', 'w') as fyml:
    readAndSetInputKeyPaths()
    for comboPaths in readComboPaths(paramsFile):
        envFile = "_{}_env{}.sh".format(name, comboPaths['paramId'])
        logging.info("Make '{}'".format(envFile))
        with open(envFile, 'w') as f:
            f.write('# Parameter combination {}\n'.format(comboPaths['paramId']))
            printVertical(comboPaths['paramCombo'], '#  ', f)
            f.write('\n')

            # Generated output paths
            for key, subjectPaths in comboPaths['paths'].items():
                firstSubject = subjectPaths[0]
                if useFullPaths:
                    path = escapePath(firstSubject.path)
                else:
                    from pnlpipe_cli.subcmd.symlink import toSymlink
                    path = toSymlink(firstSubject.caseid, name, key,
                                     firstSubject.path, comboPaths['paramId'])
                f.write('export {}={}\n\n'.format(key, path))

            f.write('export caseid={}\n\n'.format(firstSubject.caseid))
            # fyml.write('caseid: {}\n'.format(subjectPaths[0].caseid))

            # Software environment
            envDicts = []
            for softname, version, _ in getSoftwareItems(comboPaths[
                    'paramCombo']):
                m = importlib.import_module('pnlpipe_software.' + softname)
                if hasattr(m, 'envDict'):
                    envDicts.append(m.envDict(version))
            softVars = pnlpipe_software.composeEnvDicts(envDicts)
            for var, val in softVars.items():
                f.write('export {}={}\n\n'.format(var, val))
            f.write("export PATH={}:$PATH\n".format(
                local.path('pnlpipe_pipelines/pnlscripts')))
