from nodes import StrctXc, DwiXc, FsInDwiDirect, FreeSurferUsingMask, T1wMaskMabs, DwiMaskHcpBet, DwiEd, UkfDefault, Wmql, TractMeasures, T2wMaskRigid, DwiEpi, getBrainsToolsPath, getUKFTractographyPath, getTractQuerierPath, getTrainingDataT1AHCCCsv, DoesNotExistException
from pipelinelib import Src
import pipelinelib

def assertKeys(pipelineName, keys):
    absentKeys = [k for k in keys if not pipelinelib.INPUT_PATHS.get(k)]
    if absentKeys:
        for key in absentKeys:
            print("{} requires '{}' set in _inputPaths.yml".format(
                pipelineName, key))
        import sys
        sys.exit(1)


def makePipeline(caseid,
                 ukfhash,
                 tqhash,
                 dwiKey='dwi',
                 t1Key='t1',
                 dwimaskKey='dwimask',
                 ukfparams=None):
    """Makes the PNL's standard pipeline. """
    print(caseid)
    print(ukfhash)
    print(tqhash)
    print(dwiKey)
    print(t1Key)

    pipeline = { 'name' : "standard PNL pipeline" }
    assertKeys(pipeline['name'], [dwiKey, t1Key])

    pipeline['t1'] = Src(caseid, t1Key)
    pipeline['dwi'] = Src(caseid, dwiKey)

    pipeline['t1xc'] = StrctXc(caseid, pipeline['t1'])
    # run DwiXc first as it's able to convert a DWI nifti to nrrd
    pipeline['dwixc'] = DwiXc(caseid, pipeline['dwi'])
    pipeline['dwied'] = DwiEd(caseid, pipeline['dwixc'])

    pipeline['dwimask'] = Src(
        caseid, dwimaskKey) if pipelinelib.INPUT_PATHS.get(
            dwimaskKey) else DwiMaskHcpBet(caseid, pipeline['dwied'])

    pipeline['t1mask'] = Src(
        caseid,
        't1mask') if pipelinelib.INPUT_PATHS.get('t1mask') else T1wMaskMabs(
            caseid, pipeline['t1xc'])

    pipeline['fs'] = FreeSurferUsingMask(caseid, pipeline['t1xc'],
                                         pipeline['t1mask'])
    pipeline['fsindwi'] = FsInDwiDirect(caseid, pipeline['fs'],
                                        pipeline['dwied'], pipeline['dwimask'])

    pipeline['ukf'] = UkfDefault(caseid, pipeline['dwied'],
                                 pipeline['dwimask'], ukfhash)

    pipeline['wmql'] = Wmql(caseid, pipeline['fsindwi'], pipeline['ukf'],
                            tqhash)
    print(pipeline['wmql'].show())
    print(pipeline['wmql'].show2())
    import sys
    sys.exit(1)

    pipeline['tractmeasures'] = TractMeasures(caseid, pipeline['wmql'])
    return pipeline
