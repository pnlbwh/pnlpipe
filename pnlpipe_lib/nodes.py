from plumbum import local
import dag
import basenode
import abc, six
import pnlpipe_config as config


def lookupInputKey(key, caseid):
    try:
        pathFormat = config.INPUT_KEYS[key]
        caseidPlaceholder = config.INPUT_KEYS.get('caseid', '{case}')
        filepath = local.path(pathFormat.replace(caseidPlaceholder, caseid))
        return filepath
    except KeyError:
        msg = """Key '{key}' not found in pnlpipe_lib.nodes.INPUT_PATHS.
Set it in pnlpipe_config.py.
""".format(key=key)
        raise Exception(msg)


@basenode.node(params=['filepath'])
class InputFile(basenode.Node):
    def output(self):
        return self.params['filepath']
