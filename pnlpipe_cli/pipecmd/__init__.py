from plumbum import cli
import sys

class ParamApp(cli.Application):
    paramid = cli.SwitchAttr(
        ['-p', '--paramid'],
        int,
        default=0,
        mandatory=False,
        help="parameter id, run pipeline only for this parameter combination")

    def validate(self, maxid):
        if maxid == 1 and self.paramid != 1:
            print("There is only one parameter combination, so parameter id can only be {}".format(1))
            sys.exit(1)
        if self.paramid > maxid or self.paramid < 0:
            print("parameter id must be between {} and {} inclusive".format(1, maxid))
            sys.exit(1)

class PipelineSubcommand(cli.Application):
    def main(self, *args):
        if args:
            print("Unknown command {0!r}".format(args[0]))
            return 1
        if not self.nested_command:
            print("No command given")
            return 1  # error exit code
