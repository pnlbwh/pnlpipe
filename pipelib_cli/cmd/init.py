from plumbum import local, cli
import pipelib_cli
from pipelib_cli import SRCPATHS
import logging

def checkPaths(pathsDict):
    allexist = True
    logging.info('Check keys')
    for key, path in pathsDict.items():
        logging.info('{}: {}'.format(key, path))
        if key == 'caseid':
            continue
        if not local.path(path).exists():
            logging.warning("'{}' does not exist, is this intended?".format(
                path))
            allexist = False
    if not pathsDict.get('caseid', None):
        errmsg = """'caseid' not set, make you set this so the pipeline knows how to get the paths for your other subjects.
'{}' not made""".format(inputPathsFile)
        raise Exception(errmsg)
    if allexist:
        logging.info('All paths exist.')
        return
    logging.warning(
        "Warning: Some paths don't exist for the given caseid, so pipeline may fail to run.")


def writePaths(pathsDict, outfile):
    checkPaths(pathsDict)
    with open(outfile, 'w') as f:
        yaml.safe_dump(pathsDict, f, default_flow_style=False)
    logging.info("Made '{}'".format(outfile))


def readPathsYml(pathsDir):
    pathsDict = {}
    with open(pathsDir / 'paths.yml', 'r') as f:
        try:
            relativePaths = yaml.load(f, Loader=yaml.loader.BaseLoader)
        except yaml.parser.ParserError, e:
            loggin.error(
                'Error parsing {}, is there a typo? (And are the path templates in quotes?)'.format(
                    pathsDir / 'paths.yml'),
                exc_info=True)
            sys.exit(1)
    return relativePaths


class Init(cli.Application):
    """Creates input paths yaml file for this project."""

    fromdir = cli.SwitchAttr(
        '--fromdir',
        cli.ExistingDirectory,
        help='from data directory with existing paths.yml')

    def main(self):
        if local.path(SRCPATHS).exists():
            print("'{}' already exists, won't overwrite.".format(
                SRCPATHS))
            return

        # Copy from paths.yml in another project directory
        if self.fromdir:
            dataDir = self.fromdir
            inputPaths = {}
            for key, val in readPathsYml(dataDir).items():
                if key == 'caseid':
                    inputPaths[key] = val
                else:
                    absolutePath = local.path(dataDir / val)
                    newPath = absolutePath.relative_to(
                        local.path(SRCPATHS).dirname)
                    inputPaths[key] = str(newPath)
            writePaths(inputPaths, SRCPATHS)

        # Ncurses interface
        else:
            try:
                import npyscreen

                class MakePathsApp(npyscreen.NPSApp):
                    def main(self):
                        F = npyscreen.Form(
                            name="Make a paths yaml file (TAB to autocomplete and ENTER/up/down to change fields", )
                        self.dwi = F.add(npyscreen.TitleFilename,
                                         name="dwi:",
                                         begin_entry_at=24)
                        self.t1 = F.add(npyscreen.TitleFilename,
                                        name="t1:",
                                        begin_entry_at=24)
                        #self.dwimask = F.add(npyscreen.TitleFilename, name = "dwimask:", begin_entry_at=24)
                        self.t2 = F.add(npyscreen.TitleFilename,
                                        name="t2:",
                                        begin_entry_at=24)
                        self.caseid = F.add(npyscreen.TitleText,
                                            name="caseid:",
                                            begin_entry_at=24)

                        # This lets the user interact with the Form.
                        F.edit()

                NcursesApp = MakePathsApp()
                NcursesApp.run()
                inputPaths = {'caseid': NcursesApp.caseid.value}
                for key in ['dwi', 't1', 't2']:
                    if getattr(NcursesApp, key).value:
                        inputPaths[key] = getattr(NcursesApp, key).value
                writePaths(inputPaths, SRCPATHS)
            except ImportError:
                raise Exception(
                    """Could not import npyscreen for ncurses interface, instead use a
text editor to make the yaml file ({}), with this format:

    t1: /project/dir/001/001-t1.ext
    dwi: /project/dir/001/001-dwi.ext
    caseid: 001""".format(SRCPATHS))
