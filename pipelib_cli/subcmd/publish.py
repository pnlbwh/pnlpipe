from plumbum import cli
from pipelib_cli import readAndSetSrcPaths
from pipelib_cli.params import readComboPaths

def csvFromDict(d):
    s = ""
    hdr = 'project,projectPath,grantId,paramId,caselist,param,paramValue'
    row = ','.join(d.values())
    return hdr + '\n' + row


class Publish(cli.Application):
    def main(self):
        readAndSetSrcPaths()
        combos = readComboPaths(self.parent.paramsFile,
                                    self.parent.makePipeline)
        for combo in combos:
            print (combo['paramCombo'])
