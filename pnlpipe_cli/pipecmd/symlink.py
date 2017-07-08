from __future__ import print_function
from plumbum import cli, local
from pnlpipe_cli import printVertical
from ..readparams import read_grouped_combos, make_pipeline
import logging
import pnlpipe_lib
import sys
import os
import os.path
import fnmatch
import pnlpipe_config as config


def rawgz_symlink(nhdr, symlink):
    nhdr = local.path(nhdr)
    symlink = local.path(symlink)
    if nhdr.with_suffix('.raw').exists():
        raise Exception(
            'Trying to symlink to a nhdr/raw file, gzip it first ({}).'.format(
                nhdr))
    rawgz = nhdr.with_suffix('.raw.gz')
    if not rawgz.exists():
        raise Exception("Can't find .raw.gz for '{}'".format(nhdr))
    return { (symlink.dirname / rawgz.name) : rawgz }


MULTI_SYMLINKS = {'.nhdr': rawgz_symlink}


def make_symlink(src, symlink):
    src.symlink(symlink)
    for ext, extra_symlink_fn in MULTI_SYMLINKS.items():
        if src.endswith(ext):
            extra_symlinks = extra_symlink_fn(src, symlink)
            for extra_symlink, extra_src in extra_symlinks.items():
                extra_src.symlink(extra_symlink)
    provenance = local.path(src + '.provenance')
    if provenance.exists():
        provenance.symlink(symlink + '.provenance')


def to_symlink(node, tag, pipeline_name, paramid):
    nodepath = local.path(node.output())
    ext = '.'.join(nodepath.suffixes[-2:])
    filename = '{}-{}{}{}'.format(tag, pipeline_name, paramid, ext)
    filepath = (local.path(config.OUTDIR) /
                config.node_to_filepath(node)).dirname / filename
    return filepath


class SymLink(cli.Application):
    """Make descriptively named symlinks to node outputs"""

    def main(self):
        pipename = self.parent.pipeline_name

        from plumbum.cmd import find
        for symlink in find(config.OUTDIR, '-type', 'l').split():
            if fnmatch.fnmatch(symlink, '*-{}?.*'.format(pipename)):
                for ext, multi_symlink_fn in MULTI_SYMLINKS.items():
                    if not symlink.endswith(ext):
                        continue
                    multi_symlinks = multi_symlink_fn(os.path.realpath(symlink), symlink)
                    for extra_symlink, _ in multi_symlinks.items():
                        print("Remove {}".format(extra_symlink))
                        if extra_symlink.exists():
                            os.unlink(extra_symlink)
                print("Remove {}".format(symlink))
                os.unlink(symlink)
                provenance = symlink + '.provenance'
                if os.path.exists(provenance):
                    os.unlink(provenance)

        for paramid, combo, caseids in read_grouped_combos(pipename):
            if not caseids:
                pipeline = make_pipeline(pipename, combo)
                for tag, node in pipeline.items():
                    if not node.output().exists():
                        continue
                    symlink = to_symlink(node, tag, pipename, paramid)
                    symlink.dirname.mkdir()
                    print(
                        "Make symlink '{}' --> '{}' ".format(symlink,
                                                             node.output()),
                        file=sys.stderr)
                    make_symlink(node.output(), symlink)
            else:
                print('')
                print("# Make symlinks for parameter combination {}".format(
                    paramid))
                printVertical(combo)
                print('')
                for caseid in caseids:
                    pipeline = make_pipeline(pipename, combo, caseid)
                    for tag, node in pipeline.items():
                        if not node.output().exists():
                            continue
                        symlink = to_symlink(node, tag, pipename, paramid)
                        symlink.dirname.mkdir()
                        print("'{}' --> '{}' ".format(symlink, node.output()))
                        make_symlink(node.output(), symlink)
