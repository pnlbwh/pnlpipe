from plumbum import local
if not local.path('pnlpipe_config.py').exists():
    print("'pnlpipe_config.py' missing, you can make your own by running")
    print("   cp pnlpipe_config.py.example pnlpipe_config.py")
    import sys
    sys.exit(1)
import pnlpipe_config
OUTDIR = local.path(pnlpipe_config.OUTDIR)
