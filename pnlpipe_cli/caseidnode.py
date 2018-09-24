from pnlpipe_lib import *
import pnlpipe_lib.dag as dag
from pnlpipe_software import BRAINSTools, trainingDataT1AHCC, FreeSurfer
import hashlib
from plumbum import local, FG
from pnlscripts import TemporaryDirectory, dwiconvert_py, alignAndCenter_py, atlas_py, eddy_py, bet_py, wmql_py
import pnlpipe_config
import logging
from python_log_indenter import IndentedLoggerAdapter
logger = logging.getLogger(__name__)
log = IndentedLoggerAdapter(logger, indent_char='.')

OUTDIR = local.path(pnlpipe_config.OUTDIR)


def find_caseid(root):
    return find_tag(root, 'caseid')

def _lookupInputKey(key, caseid):
    try:
        pathFormat = pnlpipe_config.INPUT_KEYS[key]
        caseid_placeholder = pnlpipe_config.INPUT_KEYS['caseid_placeholder']
        filepath = local.path(pathFormat.replace(caseid_placeholder, caseid))
        return filepath
    except KeyError as e:
        msg = """Key '{}' not found in pnlpipe_config.py:INPUT_KEYS.
It might be misspelled, or you might need to add it if it's missing.
""".format(e.args[0])
        raise Exception(msg)


def dag_filepath(node, ext, caseid_dir=True):
    caseid = find_caseid(node)
    if ext and not ext.startswith('.'):
        ext = '.' + ext
    if caseid_dir:
        return OUTDIR / caseid / showCompressedDAG(node) + ext
    return OUTDIR / showCompressedDAG(node) + ext


def hash_filepath(node, ext, caseid_dir=True, extra_words=None):
    def _hashstring(s):
        hasher = hashlib.md5()
        hasher.update(s.encode('utf-8'))
        return hasher.hexdigest()[:10]

    caseid = find_caseid(node)
    extras = [caseid] + extra_words if extra_words else [caseid]
    dagstr = dag.showDAG(node)
    for extra in extras:
        dagstr = dagstr.replace(extra, '')
    nodestem = '{}-{}-{}'.format(node.tag, '-'.join(extras),
                                 _hashstring(dagstr))
    if ext and not ext.startswith('.'):
        ext = '.' + ext

    if caseid_dir:
        return OUTDIR / caseid / (nodestem + ext)
    return OUTDIR / (nodestem + ext)


@node(params=['key', 'caseid'])
class InputPathFromKey(Node):
    """An input path found by looking up its key in INPUT_KEYS in pnlpipe_config.py
    and substituting its caseid."""

    def output(self):
        return _lookupInputKey(self.key, self.caseid)

    def show(self):
        return self.output()


class AutoOutput(Node):
    """A generated output, saved as <OUTDIR>/<caseid>/<output_path>"""

    @abc.abstractproperty
    def ext(self):
        """Extension of output"""

    def extra_output_names(self):
        """Extra words to put in output name, used by subclasses that want to put
        some of their parameters into their output filename."""
        return None

    def output(self):
        return hash_filepath(self,
                             self.ext,
                             caseid_dir=True,
                             extra_words=self.extra_output_names())


# def showCompressedDAG(node):
#     def isLeaf(n):
#         if isinstance(n, InputPathFromKey):
#             return True
#         if isinstance(n, InputFile):
#             return True
#         if not n.children:
#             return True
#         return False

#     return dag.showCompressedDAG(node, isLeaf=isLeaf)
