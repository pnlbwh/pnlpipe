#!/usr/bin/env python
import sys
import yaml
from plumbum import local, cli

def checkPaths(pathsDict):
    allexist = True
    for key, path in pathsDict.items():
        print('{}: {}'. format(key, path))
        if key == 'caseid':
            continue
        if not local.path(path).exists():
            print("'{}' does not exist, is this intended?".format(path))
            allexist = False
    print('')
    if allexist:
        print('All paths exist')
        return
    print("Warning: Some paths don't exist for the given caseid, so 'pyppl' may fail to run.")

    if not pathsDict.get('t1'):
        print("Warning: 't1' not set")
    if not pathsDict.get('dwi'):
        print("Warning: 'dwi' not set")

def writePaths(pathsDict, outfile):
    checkPaths(pathsDict)
    with open(outfile, 'w') as f:
        yaml.safe_dump(pathsDict, f, default_flow_style=False)
    print("Made '{}'".format(outfile))

def readPathsYml(pathsDir):
    pathsDict = {}
    with open(pathsDir / 'paths.yml', 'r') as f:
        try:
            relativePaths = yaml.load(f,  Loader=yaml.loader.BaseLoader)
        except yaml.parser.ParserError as err:
            print(err)
            print('Error parsing {}, is there a typo? (And are the path templates in quotes?)'.format(pathsDir/'paths.yml'))
            sys.exit(1)
    return relativePaths

class App(cli.Application):
    """
    Makes a yaml file which is a dictionary of paths to a single subject's
    data (typically a t1, dwi, and a dwi mask).

    """
    out = cli.SwitchAttr(['-o', '--output'], cli.NonexistentPath, help="Output yaml filename", default="paths.yml")

    def main(self, *args):
        if args:
            print("Unknown command {0!r}".format(args[0]))
            return 1
        if not self.nested_command:
            print("No command given")
            return 1  # error exit code

@App.subcommand("fromdir")
class FromExisting(cli.Application):
    """Creates a yaml file from an pre-existing one."""

    @cli.positional(cli.ExistingDirectory)
    def main(self, dataDir):

        # Make new paths relative to the ones in the input paths.yml
        inputPaths = {}
        for key, val in readPathsYml(dataDir).items():
            if key == 'caseid':
                inputPaths[key] = val
            else:
                absolutePath = local.path(dataDir / val)
                newPath = absolutePath.relative_to(local.path(self.parent.out).dirname)
                inputPaths[key] = str(newPath)

        writePaths(inputPaths, self.parent.out)

@App.subcommand("ncurses")
class Ncurses(cli.Application):
    """Creates a yaml file from an ncurses interface."""

    def main(self):
        try:
            import npyscreen
            class MakePathsYml(npyscreen.NPSApp):
                def main(self):
                    F  = npyscreen.Form(name = "Make a paths yaml file",)
                    dwi = F.add(npyscreen.TitleFilename, name = "dwi:", begin_entry_at=24)
                    t1 = F.add(npyscreen.TitleFilename, name = "t1:", begin_entry_at=24)
                    dwimask = F.add(npyscreen.TitleFilename, name = "dwimask (optional):", begin_entry_at=24)
                    self.t2 = F.add(npyscreen.TitleFilename, name = "t2 (optional):", begin_entry_at=24)
                    caseid  = F.add(npyscreen.TitleText, name = "caseid:", begin_entry_at=24)

                    # This lets the user interact with the Form.
                    F.edit()


            NcursesApp = MakePathsYml()
            NcursesApp.run()
            inputPaths = {
                'dwi': NcursesApp.dwi.value
            }

            writePaths(inputPaths, self.parent.out)
        except ImportError:
            print("""
Could not import npyscreen for ncurses interface, instead use a
text editor to make the yaml file ({}), with this format:

            t1: /project/dir/001/001-t1.ext
            dwi: /project/dir/001/001-dwi.ext
            caseid: 001

('t1', 'dwi', and 'caseid' are mandatory, 't2' and 'dwimask' are optional)
            """.format(self.parent.out))
            sys.exit(1)


if __name__ == '__main__':
    App.run()
