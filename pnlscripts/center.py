#!/usr/bin/env python

from __future__ import print_function
import operator
from util import logfmt, ExistingNrrd
from plumbum import local, cli, FG
from plumbum.cmd import unu
import re
import fileinput

import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logfmt(__file__))

def get_spc_dirs(s):
    match = re.search(
  'space directions: \((?P<xvec>(.*))\) \((?P<yvec>(.*))\) \((?P<zvec>(.*))\)',
        s)
    xvec = [float(x) for x in match.group('xvec').split(',')]
    yvec = [float(x) for x in match.group('yvec').split(',')]
    zvec = [float(x) for x in match.group('zvec').split(',')]
    # take transpose
    col1=[xvec[0],yvec[0],zvec[0]]
    col2=[xvec[1],yvec[1],zvec[1]]
    col3=[xvec[2],yvec[2],zvec[2]]
    return (col1, col2, col3)

def get_sizes(s):
    for line in s.splitlines():
        if "sizes:" in line:
            words = line.split()
            size_x, size_y, size_z = map(float, (words[1], words[2], words[3]))
            return (size_x, size_y, size_z)
    return (None, None, None)

def get_origin(s):
    for line in s.splitlines():
        if "space origin:" in line:
            return line
    return None

def dot_product(v1, v2):
    return [a*b for (a,b) in zip(v1, v2)]

def centered_origin(hdr):
    spc_dirs = get_spc_dirs(hdr)
    sizes = get_sizes(hdr)
    print("space directions: " + str(spc_dirs))
    print("sizes: " + str(sizes))
    print(get_origin(hdr))
    new_origin = []
    for dir in spc_dirs:
        sizes2 = [(x-1)/2  for x in sizes]
        tuple(sizes2)
        dp = dot_product(sizes2, dir)
        dp_abs = [abs(x) for x in dp]
        maxmin_elem = dp_abs.index(max(dp_abs))
        new_origin.append(-dp[maxmin_elem])
    print("new origin: " + str(new_origin))
    return new_origin

def replace_line_in_file(afile, match_string, replace_with):
    for line in fileinput.FileInput(afile, inplace=1):
        if match_string in line:
            line = replace_with
        print(line,end='')

class App(cli.Application):
    """Centers a nrrd."""

    nrrd = cli.SwitchAttr(['-i', '--infile'], ExistingNrrd, help='a 3d or 4d nrrd image', mandatory=True)
    out = cli.SwitchAttr(['-o', '--outfile'], help='a 3d or 4d nrrd image', mandatory=True)

    def main(self):
        hdr = unu('head', self.nrrd)[:-1]
        new_origin = centered_origin(hdr)
        unu('save', '-e', 'gzip', '-f', 'nrrd', '-i', self.nrrd, '-o', self.out)
        replace_line_in_file(self.out, "space origin: ", "space origin: (%s, %s, %s)\n" % tuple(new_origin))

if __name__ == '__main__':
    App.run()
