from plumbum import local, FG
import os
from pnlscripts.util import TemporaryDirectory
from plumbum.cmd import unu

dwidicoms = local.path(os.getenv('dwidicoms'))
dwiconvert = local['../dwiconvert.py']

def run(input, output):
    dwiconvert['-i', input, '-o', output] & FG

def test_DWIConvert():
    with TemporaryDirectory() as tmpdir:
        fsl = tmpdir / 'dwi.nii.gz'
        nrrd = tmpdir / 'dwi.nrrd'
        nrrdFromFSl = tmpdir / 'dwi-from-fsl.nrrd'
        run(dwidicoms, fsl)
        run(dwidicoms, nrrd)
        run(fsl, nrrdfromFsl)
        output = unu('diff', nrrd, nrrdFromFSl)
        assert not 'differ' in output
