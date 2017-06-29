#!/usr/bin/env python
try:
    from plumbum import local, FG, cli
except ImportError:
    print('Couldn\'t import plumbum')
    print(
        'Did you forget to load python environment? (e.g. source activate pnlpipe)')
import pp_software
import logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)5s - %(name)s %(message)s', datefmt="%Y-%m-%d %H:%M")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)5s - %(name)s:  %(message)s',
    datefmt="%Y-%m-%d %H:%M")
logger = logging.getLogger(__name__)

import pp_cli.subcmd
import pp_cli.cmd.install


class App(cli.Application):
    def main(self, *args):
        if args:
            print("Unknown command {0!r}".format(args[0]))
            return 1
        if not self.nested_command:
            print("No command given")
            return 1  # error exit code


def classSoftwareFactory(name,
                         makeFn,
                         BaseClass=pp_cli.cmd.install.SoftwareCommand):
    def wrapFunction(self, *args, **kwargs):
        return make(*args, **kwargs)

    newclass = type(name, (BaseClass, ), {"make": wrapFunction})
    return newclass


def pipelineModules():
    import pkgutil
    import pp_pipelines
    from os.path import isfile
    for importer, modname, ispkg in pkgutil.iter_modules(pp_pipelines.__path__):
        if modname.startswith('pipeline_'):
            yield importer.find_module(modname).load_module(modname)


def classFactory(name,
                 makePipelineFn,
                 statusFn,
                 defaultTarget,
                 BaseClass=pp_cli.subcmd.PipelineSubcommand):
    def wrappedMakePipeline(self, *args, **kwargs):
        return makePipelineFn(*args, **kwargs)

    paramsFile = local.path(name + '.params')
    newclass = type(name, (BaseClass, ), {"name": name,
                                          "makePipeline": wrappedMakePipeline,
                                          "makePipeline_orig": makePipelineFn,
                                          "paramsFile": paramsFile,
                                          "defaultTarget": defaultTarget})

    if statusFn:

        def wrappedStatus(self, *args, **kwargs):
            return statusFn(*args, **kwargs)

        setattr(newclass, 'status', wrappedStatus)
    return newclass


if __name__ == '__main__':
    import pp_cli.cmd.init
    import pp_cli.cmd.export
    import pp_cli.subcmd.init
    import pp_cli.subcmd.make
    import pp_cli.subcmd.run
    import pp_cli.subcmd.status
    import pp_cli.subcmd.symlink
    import pp_cli.subcmd.ls
    import pp_cli.subcmd.missing
    import pp_cli.subcmd.keys

    App.subcommand("init", pp_cli.cmd.init.Init)
    App.subcommand("install", pp_cli.cmd.install.SoftwareCommand)
    App.subcommand("export", pp_cli.cmd.export.Export)

    for m in pipelineModules():
        name = m.__name__[9:]
        statusFn = getattr(m, 'status', None)
        defaultTarget = getattr(m, 'DEFAULT_TARGET', None)
        SubcommandClass = classFactory(name, m.makePipeline, statusFn,
                                       defaultTarget)
        App.subcommand(name, SubcommandClass)
        SubcommandClass.subcommand("run",     pp_cli.subcmd.run.Run)
        SubcommandClass.subcommand("make",    pp_cli.subcmd.make.Make)
        SubcommandClass.subcommand("init",    pp_cli.subcmd.init.Init)
        SubcommandClass.subcommand("symlink", pp_cli.subcmd.symlink.SymLink)
        SubcommandClass.subcommand("status",  pp_cli.subcmd.status.Status)
        SubcommandClass.subcommand("ls",      pp_cli.subcmd.ls.Ls)
        SubcommandClass.subcommand("missing", pp_cli.subcmd.missing.Missing)
        SubcommandClass.subcommand("keys",    pp_cli.subcmd.keys.Keys)

    App.run()
