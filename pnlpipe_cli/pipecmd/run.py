from __future__ import print_function
from plumbum import local, FG, cli
import yaml
import pnlpipe_config
import sys
import logging
log = logging.getLogger(__name__)
from pnlpipe_lib import *
from . import ParamApp
from ..display import printVertical
from ..readparams import read_grouped_combos, make_pipeline, get_software
import pnlpipe_pipelines
import pnlpipe_software


def _concat(l):
    return l if l == [] else [item for sublist in l for item in sublist]

class Run(ParamApp):
    """Runs pipeline"""

    want = cli.SwitchAttr(
        ['-w', '--want'], help='name of target node to build, e.g. fsindwi')

    keepGoing = cli.Flag(
        ['-k'],
        default=False,
        help="keep going if possible when there's an exception")

    question = cli.Flag(
        ['-q', '--question'], default=False, help="Update no target, just print if up to date or not")

    def main(self, *arg_caseids):

        pipeline_name = self.parent.pipeline_name
        log.info('Run {} pipeline'.format(pipeline_name))
        target = self.want
        if not target:
            target = pnlpipe_pipelines.default_target(pipeline_name)

        log.info('Check that prerequisite software exists')
        missing_modules = []
        missing_paths = []
        grouped_combos = read_grouped_combos(pipeline_name, assert_valid_combos=True)

        self.validate(len(grouped_combos))

        # Check that prerequisite software is installed
        software = set(_concat([get_software(combo).items() for (_,combo,_) in grouped_combos]))
        for name, version in software:
            modulefile = pnlpipe_software.module_file(name)
            if not modulefile.exists():
                missing_modules.append(modulefile)
                continue
            module = pnlpipe_software.import_module(name)
            softpath = local.path(module.get_path(version))
            if not softpath.exists():
                missing_paths.append(module.get_path(version))
                continue
            log.info("{} exists".format(softpath))

        for f in missing_modules:
            log.critical("missing {}".format(f))

        for p in missing_paths:
            log.critical("missing: {}".format(p))

        if missing_modules:
            sys.exit(1)

        if missing_paths:
            errmsg = """
Some pnlpipe_software components are missing and so some parts of the pipeline won't run.
Run './pnlpipe {} setup' to build all prequisite pnlpipe_software.
            """.format(pipeline_name)
            errmsgFS = """
Some pnlpipe_software components are missing and so some parts of the pipeline won't run.
Run './pnlpipe {} setup' to build all prequisite pnlpipe_software and make sure the environment variable FREESURFER_HOME is set.
            """.format(pipeline_name)

            # TODO remove ad hoc message for FreeSurfer?
            for soft in missing_paths:
                if 'FREESURFER_HOME' in soft:
                    print(errmsgFS)
                    sys.exit(1)
                    # raise Exception(errmsgFS)
            # raise Exception(errmsg)
            print(errmsg)
            sys.exit(1)

        for paramid, combo, caseids in grouped_combos:
            if self.paramid and paramid != self.paramid:
                continue
            print('')
            print("## Pipeline {} ({} cases)".format(paramid, len(caseids)))
            caseids = arg_caseids if arg_caseids else caseids
            print('')
            print('Parameters:')
            printVertical(dict(combo, caseids=caseids), keys=combo.keys() + ['caseids'])
            for caseid in caseids:
                # print(['caseid']+combo.keys())
                # print(dict(combo,caseid=caseid))
                print('')
                # fullCombo = {}
                # fullCombo.update(combo)
                # fullCombo[OBSID_KEY] = caseid
                # print('Parameters:')
                # printVertical(fullCombo, keys=[OBSID_KEY] + combo.keys())
                print('Update caseid: {}'.format(caseid))
                pipeline = make_pipeline(pipeline_name, combo, caseid=caseid)
                log.info("Make target tagged '{}'".format(target))
                if self.question:
                    nodeAndReason = upToDate(pipeline[target])
                    if nodeAndReason:
                        print("'{}' is stale".format(pipeline[target].show()))
                        print("Reason: {}: {}".format(nodeAndReason[0].show(), nodeAndReason[1]))
                        print()
                    else:
                        print("{}: is up to date.".format(pipeline[target].show()))
                else:
                    update(pipeline[target])

            # try:
            #     pnlpipe_lib.update(pipeline[want])
            # except Exception as e:
            #     if self.keepGoing:
            #         continue
            #     else:
            #         raise(e)
