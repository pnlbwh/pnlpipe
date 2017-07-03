from plumbum import local, FG, cli
import yaml
import logging
import pnlpipe
from pp_cli import readAndSetSrcPaths, printVertical
from pp_cli.params import readParamCombos, assertValidParamCombos, \
    getSoftwareItems
import importlib

class Run(cli.Application):

    want = cli.SwitchAttr(
        ['-w', '--want'], help='target node to build, e.g. fsindwi')
    keepGoing = cli.Flag(
        ['-k'], default=False, help="keep going if possible when there's an exception")
    paramId = cli.SwitchAttr(['-p'], int, mandatory=False, help="parameter id, run pipeline only for this parameter combination")

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
                module = importlib.import_module('pp_software.' + softname)
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
Some pp_software components are missing and so some parts of the pipeline won't run.
Run './pipe {} make' to build all prequisite pp_software.
            """.format(self.parent.name)
            errmsgFS = """
Some pp_software components are missing and so some parts of the pipeline won't run.
Run './pipe {} make' to build all prequisite pp_software and make sure FREESURFER_HOME is set.
            """.format(self.parent.name)
            for soft in missingSoftware:
                if 'FREESURFER_HOME' in soft:
                    raise Exception(errmsgFS)
            raise Exception(errmsg)

        if not self.want:
            if not self.parent.defaultTarget:
                errmsg = """
'pp_pipelines/pipeline_{}.py' doesn't have 'DEFAULT_TARGET' defined, set this in 'makePipeline(...)'."
E.g. DEFAULT_TARGET = 'tractmeasures'""".format(self.parent.name,
                                                self.parent.name)
                raise Exception(errmsg)
            want = self.parent.defaultTarget
        else:
            want = self.want
        logging.info('Make target {}'.format(want))

        for paramCombo, caseids in paramCombos:
            if self.paramId and paramCombo != self.paramId:
                continue
            caseids = commandLineCaseids if commandLineCaseids else caseids
            for caseid in caseids:
                logging.info('Running {} pipeline'.format(self.parent.name))
                print("# Subject ID " + caseid)
                printVertical(paramCombo)
                args = dict(paramCombo, caseid=caseid)
                args = {k:v for k,v in args.items() if not k.startswith('_')}
                pipeline = self.parent.makePipeline(**args)
                pnlpipe.update(pipeline[want])
                # try:
                #     pnlpipe.update(pipeline[want])
                # except Exception as e:
                #     if self.keepGoing:
                #         continue
                #     else:
                #         raise(e)
