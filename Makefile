ifeq ($(soft),)
  $(error Export 'soft' first (This is where e.g. BRAINSTools and training data are/will be installed))
endif

##############################################################################
BTHASH=41353e8
TQHASH= e045eab
UKFHASH=421a7ad

UKFTRACTOGRAPHY=$(soft)/UKFTractography-$(UKFHASH)
BRAINSTOOLS=$(soft)/BRAINSTools-bin-$(BTHASH)/antsRegistration
TRACT_QUERIER=$(soft)/tract_querier-$(TQHASH)/README.md
TRAININGT1s=$(soft)/trainingDataT1AHCC/trainingDataT1AHCC-hdr.csv


##############################################################################
# Run pipeline
ifeq ($(subcmd),)
# the default, e.g.
#    make
#    make args="--want fsindwi" case001
	RUN=./pyppl pnl --ukfhash $(UKFHASH) --bthash $(BTHASH) --tqhash $(TQHASH) $(args)
else
# custom command, e.g.
#    make subcmd=custom
	RUN=./pyppl $(subcmd) $(args)
endif

.PHONY: all caselist

all: _inputPaths.yml | $(UKFTRACTOGRAPHY) $(TRACT_QUERIER) $(BRAINSTOOLS) $(TRAININGT1S)
	$(RUN)

%:
	$(RUN) $*

%-bsub4: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 4 $(RUN) $*
%-bsub8: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 8 $(RUN) $*
%-bsub16: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 16 $(RUN) $*

caselist: caselist.txt
	while read subj; do make $$subj-bsub8; done < caselist.txt

caselist.txt:
	$(error First make a caselist.txt with your subject ids, then run again)

##############################################################################
# Make Input Data Paths
.PHONY: inputpaths

inputpaths: _inputPaths.yml

_inputPaths.yml:
ifeq ($(fromdir),)
	@echo \'fromdir\' not set, so create new $@ using makepathyml.py\'s ncurses interface
	./pnlscripts/makepathsyml.py -o $@ ncurses
else
	./pnlscripts/makepathsyml.py -o $@ fromdir $(fromdir)
endif

##############################################################################
# Setup Pipeline Software
.PHONY: software
software: $(UKFTRACTOGRAPHY) $(TRACT_QUERIER) $(BRAINSTOOLS) $(TRAININGT1S)
$(UKFTRACTOGRAPHY): ; ./pnlscripts/software.py --commit $(UKFHASH) ukftractography
$(BRAINSTOOLS): ; ./pnlscripts/software.py --commit $(BTHASH) brainstools
$(TRACT_QUERIER): ; ./pnlscripts/software.py --commit $(TQHASH) tractquerier
$(TRAININGT1S): ; ./pnlscripts/software.py trainingt1s

##############################################################################
# Make Python Environment
.PHONY: conda env nix

venv: _venv
nix: _pip_packages.nix ; @echo "Now run 'nix-shell'"
conda: _environment.yml
	conda env create -f $<
	@echo "Now run `source activate pyppl`"

_venv: _requirements.txt
	virtualenv $@; $@/bin/pip install -r $<
	@echo "Now run `source $@/bin/activate`"

_pip_packages.nix: _requirements.txt
	if [ ! -d "_pip2nix" ]; then \
		git clone https://github.com/acowley/pip2nix _pip2nix; \
  fi
	cd _pip2nix; nix-shell --run 'pip2nix ../requirements.txt -o ../_pip_packages.nix'

#########################################################
# Shell script to setup environment
.PHONY: env
env: _env.sh
_env.sh: $(BRAINSTOOLS) $(TRACT_QUERIER)
	sed "s,__BRAINSTOOLS__,$(dir $(BRAINSTOOLS))," ._env.sh > $@
	sed -i "s,__UKFTRACTOGRAPHY__,$(UKFTRACTOGRAPHY),"  $@
	sed -i "s,__TRACT_QUERIER__,$(dir $(TRACT_QUERIER))," $@
	@echo "Now run 'source _env.sh'"

#########################################################
# Makefile helper functions

# Params:
#   1. Variable name(s) to test.
#   2. (optional) Error message to print.
check_defined = \
    $(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
    $(if $(value $1),, \
      $(error Undefined $1$(if $2, ($2))))
