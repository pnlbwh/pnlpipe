from plumbum import local, FG, cli
import yaml
import logging
import pipelib
from pipelib_cli import readAndSetSrcPaths, printVertical
from pipelib_cli.params import readParamCombos, assertValidParamCombos, \
    getSoftwareItems
import importlib

class Run(cli.Application):

    want = cli.SwitchAttr(
        ['-w', '--want'], help='target node to build, e.g. fsindwi')

    def main(self, *commandLineCaseids):
        readAndSetSrcPaths()
        paramCombos = readParamCombos(self.parent.paramsFile)
        assertValidParamCombos(paramCombos, self.parent.paramsFile)

        logging.info('Check that prerequisite software exists')
        missingSoftwareModules = []
        missingSoftware = []
        for (paramCombo, _) in paramCombos:
            for softname, version, modulefile in getSoftwareItems(paramCombo):
                if not modulefile.exists():
                    missingSoftwareModules.append(modulefile)
                    continue
                module = importlib.import_module('software.' + softname)
                if not local.path(module.getPath(version)).exists():
                    missingSoftware.append(module.getPath(version))

        for f in missingSoftwareModules:
            logging.warning("missing {}".format(f))
        for p in missingSoftware:
            logging.warning("missing: {}".format(p))
        if missingSoftwareModules:
            sys.exit(1)
        if missingSoftware:
            errmsg = """
Some software components are missing and so some parts of the pipeline won't run.
Run './pipe {} make' to build all prequisite software.
            """.format(self.parent.name)
            errmsgFS = """
Some software components are missing and so some parts of the pipeline won't run.
Run './pipe {} make' to build all prequisite software and make sure FREESURFER_HOME is set.
            """.format(self.parent.name)
            for soft in missingSoftware:
                if 'FREESURFER_HOME' in soft:
                    raise Exception(errmsgFS)
            raise Exception(errmsg)

        if not self.want:
            if not self.parent.defaultTarget:
                errmsg = """
'pipelines/pipeline_{}.py' doesn't have 'DEFAULT_TARGET' defined, set this in 'makePipeline(...)'."
E.g. DEFAULT_TARGET = 'tractmeasures'""".format(self.parent.name,
                                                self.parent.name)
                raise Exception(errmsg)
            want = self.parent.defaultTarget
        else:
            want = self.want
        logging.info('Make target {}'.format(want))

        for paramCombo, caseids in paramCombos:
            caseids = commandLineCaseids if commandLineCaseids else caseids
            for caseid in caseids:
                logging.info('Running {} pipeline'.format(self.parent.name))
                print("# Subject ID " + caseid)
                printVertical(paramCombo)
                args = dict(paramCombo, caseid=caseid)
                pipeline = self.parent.makePipeline(**args)
                pipelib.update(pipeline[want])
