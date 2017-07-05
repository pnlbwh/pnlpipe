from pnlpipe_lib import InputKey, GeneratedNode, needDeps
from plumbum import local

class Wc(GeneratedNode):
    def __init__(self, caseid, filelist):
        self.deps = [filelist]
        self.ext = '.txt'
        GeneratedNode.__init__(self, locals())
    def build(self, db):
        needDeps(self, self.deps, db)
        with open(self.filelist.path(), 'r') as f:
            lines = f.read().splitlines()
        files = [local.cwd/line for line in lines]
        words = []
        for file in files:
            with open(file, 'r') as f:
                words = words + f.read().split()
        with open(self.path(), 'w') as f:
            f.write(str(len(words)))

DEFAULT_TARGET = 'wc'

def makePipeline(caseid, param1, param2):

    p = {}
    p['filelist'] = InputKey(caseid, 'filelist')
    p['wc'] = Wc(caseid, p['filelist'])
    return p
