#!/usr/bin/env python
from __future__ import print_function

# check python version compatibility
import sys
if sys.version_info.major!=2:
    raise EnvironmentError('Requires Python 2 interpreter')

from plumbum import local, cli, FG
import itertools

def concat(l):
    return l if l == [] else [item for sublist in l for item in sublist]

class App(cli.Application):
    """Make html page of rendered wmql tracts. """

    wmqldirs = cli.SwitchAttr(
        ['-i'],
        help='list of wmql directories, must be enclosed within quotes',
        mandatory=True)

    caseids = cli.SwitchAttr(
        ['-s'],
        help='list of subject ids corrsponding to wmql directories, must be enclosed within quotes',
        mandatory=True)

    out = cli.SwitchAttr(
        ['-o'],
        cli.NonexistentPath,
        help='Output directory',
        mandatory=True)

    def main(self):
        try:
            wm_quality_control_tractography = local['wm_quality_control_tractography.py']
        except:
            raise EnvironmentError('wm_quality_control_tractography.py not in PATH, '
                                   'see http://dmri.slicer.org/atlases/ for installation instruction.')
        tuples = zip(self.caseids.split(), map(local.path, self.wmqldirs.split()))
        vtks = [(caseid, vtk) for (caseid, d) in tuples for vtk in d // '*.vtk']
        keyfn = lambda s,x : local.path(x).name[:-4]
        groupedvtks = itertools.groupby(sorted(vtks, key=keyfn), key=keyfn)
        self.out.mkdir()
        for group, vtks in groupedvtks:
            vtkdir = self.out / group
            qcdir = self.out / (group + '-qc')
            print("Make symlinks for vtk group {}".format(group))
            vtkdir.mkdir()
            for (caseid, vtk) in vtks:
                symlink = vtkdir / (vtk.name[:-4] + '_' + caseid + '.vtk')
                print("Make symlink for caseid '{}': {}".format(caseid, symlink))
                vtk.symlink(symlink)
            print("Render tracts for vtk group {}".format(group))
            wm_quality_control_tractography[vtkdir, qcdir] & FG

if __name__ == '__main__':
    App.run()
