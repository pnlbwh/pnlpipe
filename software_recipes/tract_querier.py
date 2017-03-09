from software_recipes.__lib import downloadGithubRepo, getCommitInfo, getSoftDir, checkExists
from plumbum import local
from plumbum.cmd import cmake, make, chmod
import logging
from pnlscripts.util import TemporaryDirectory

def make(commit):
    """Downloads a lean version of tract_querier. Output is '$soft/tract_querier-<commit>'."""
    dest = getSoftDir()

    if commit != 'master':
        out = local.path(dest / 'tract_querier-' + commit)
        if checkExists(out):
            return

    with TemporaryDirectory() as tmpdir, local.cwd(tmpdir):
        repo = downloadGithubRepo('demianw/tract_querier', commit)
        sha, date = getCommitInfo(repo)
        out = local.path(dest / 'tract_querier-' + sha)
        if checkExists(out):
            return

        # save space
        (repo / 'doc').delete()
        (repo / '.git').delete()

        logging.info("Make '{out}'".format(**locals()))
        repo.move(out)

    chmod('-R', 'a-w', out)
    chmod('a-w', out)
    date_symlink = dest / 'tract_querier-' + date
    out.symlink(date_symlink)
