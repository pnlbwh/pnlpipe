from __future__ import print_function
from plumbum import local, FG, cli
import yaml
import sys
import logging
logger = logging.getLogger(__name__)
from pnlpipe_lib import *
from ..display import printVertical
from ..readparams import read_grouped_combos, software_params, make_pipeline
import pnlpipe_pipelines
import pnlpipe_software
import importlib


class Run(cli.Application):
    """Runs pipeline"""

    want = cli.SwitchAttr(
        ['-w', '--want'], help='name of target node to build, e.g. fsindwi')

    keepGoing = cli.Flag(
        ['-k'],
        default=False,
        help="keep going if possible when there's an exception")

    param_id = cli.SwitchAttr(
        ['-p', '--paramid'],
        int,
        mandatory=False,
        help="parameter id, run pipeline only for this parameter combination")

    def main(self, *arg_caseids):
        pipeline_name = self.parent.pipeline_name
        target = self.want
        if not target:
            target = pnlpipe_pipelines.default_target(pipeline_name)

        logger.info('Check that prerequisite software exists')
        missing_software_modules = []
        missing_software = []
        grouped_combos = read_grouped_combos(pipeline_name, assert_valid_combos=True)

        # Check that prerequisite software is installed
        for paramid, combo, caseids in grouped_combos:
            for softname, version in software_params(combo).items():
                modulefile = pnlpipe_software.module_file(softname)
                if not modulefile.exists():
                    missing_software_modules.append(modulefile)
                    continue
                module = pnlpipe_software.import_module(softname)
                if not local.path(module.get_path(version)).exists():
                    missing_software.append(module.get_path(version))

        for f in missing_software_modules:
            logger.warning("missing {}".format(f))
        for p in missing_software:
            logger.warning("missing: {}".format(p))
        if missing_software_modules:
            sys.exit(1)
        if missing_software:
            errmsg = """
Some pnlpipe_software components are missing and so some parts of the pipeline won't run.
Run './pipe {} make' to build all prequisite pnlpipe_software.
            """.format(pipeline_name)
            errmsgFS = """
Some pnlpipe_software components are missing and so some parts of the pipeline won't run.
Run './pipe {} make' to build all prequisite pnlpipe_software and make sure FREESURFER_HOME is set.
            """.format(pipeline_name)

            # TODO ad hoc check for FreeSurfer
            for soft in missing_software:
                if 'FREESURFER_HOME' in soft:
                    raise Exception(errmsgFS)
            raise Exception(errmsg)

        for paramid, combo, caseids in grouped_combos:

            if self.param_id and paramid != self.param_id:
                continue

            # if parameters don't have an observation id type key
            if not caseids:
                logger.info('Running {} pipeline'.format(pipeline_name))
                printVertical(combo)
                pipeline = make_pipeline(pipeline_name, combo)
                # logger.info("Make target '{}'".format(pipeline[target].show()))
                update(pipeline[target])
                continue
            else:
                caseids = arg_caseids if arg_caseids else caseids
                for caseid in caseids:
                    logger.info('Running {} pipeline'.format(pipeline_name))
                    print("# Case '{}'".format(caseid), file=sys.stderr)
                    printVertical(combo)
                    pipeline = make_pipeline(pipeline_name, combo, caseid)
                    logger.info("Make target tagged '{}'".format(target))
                    update(pipeline[target])

                # try:
                #     pnlpipe_lib.update(pipeline[want])
                # except Exception as e:
                #     if self.keepGoing:
                #         continue
                #     else:
                #         raise(e)
