from plumbum import local, cli
import pipelib_cli
from pipelib_cli import SRCPATHS, readAndSetSrcPaths, printVertical
from pipelib_cli.params import readParamCombos, readComboPaths, getSoftwareItems
import importlib
import logging
import software


class Make(cli.Application):
    """ Builds necessary software for pipeline. """

    def main(self):
        if not self.parent.paramsFile.exists():
            raise Exception(
                "'{}' doesn't exist, make it first with './pipe {} init'".format(
                    self.parent.paramsFile, self.parent.__class__.__name__))

        logging.info("Build prerequisite software")
        for (paramCombo, _) in readParamCombos(self.parent.paramsFile):
            for softname, commit, modulefile in getSoftwareItems(paramCombo):
                if not modulefile.exists():
                    raise Exception("{} does not exist".format(modulefile))
                module = importlib.import_module('software.' + softname)
                logging.info("Make {}".format(module.getPath(commit)))
                module.make(commit)

        logging.info("Make shell environment files")
        makeEnvFiles(self.parent.name, self.parent.paramsFile,
                     self.parent.makePipeline)

def escapePath(filepath):
    return filepath.__str__().replace('(', '\(').replace(')', '\)')


def makeEnvFiles(name, paramsFile, makePipelineFn):
    # first delete existing files in case they are stale
    for f in local.cwd.glob(name + '*.sh'):
        f.delete()
    # with open('outputPaths.yml', 'w') as fyml:
    readAndSetSrcPaths()
    for comboPaths in readComboPaths(paramsFile, makePipelineFn):
        envFile = "_{}_env{}.sh".format(name, comboPaths['id'])
        logging.info("Make '{}'".format(envFile))
        with open(envFile, 'w') as f:
            f.write('# Parameter combination {}\n'.format(comboPaths['id']))
            printVertical(comboPaths['paramCombo'], '#  ', f)
            f.write('\n')

            # Generated output paths
            for key, subjectPaths in comboPaths['paths'].items():
                firstSubject = subjectPaths[0]
                f.write('{}={}\n\n'.format(key, escapePath(firstSubject.path)))
                # fyml.write('{}: {}\n'.format(key, subjectPaths[0].path.relative_to(local.cwd)))
            f.write('caseid={}\n\n'.format(firstSubject.caseid))
            # fyml.write('caseid: {}\n'.format(subjectPaths[0].caseid))

            # Software environment
            envDicts = []
            for softname, version, _ in getSoftwareItems(comboPaths[
                    'paramCombo']):
                m = importlib.import_module('software.' + softname)
                if hasattr(m, 'envDict'):
                    envDicts.append(m.envDict(version))
            softVars = software.composeEnvDicts(envDicts)
            for var, val in softVars.items():
                f.write('{}={}\n\n'.format(var, val))
            f.write("PATH={}:$PATH\n".format(
                local.path('pipelines/pnlscripts')))
