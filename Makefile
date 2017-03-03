ifeq ($(soft),)
  $(error Export 'soft' first (This is where e.g. BRAINSTools and training data are/will be installed))
endif

RUN := ./pyppl std

##############################################################################
# Run pipeline
#
# E.g
#    make           # runs default caseid in _inputPaths.yml
#    make case0001
#    make case0001-bsub8
#    make caselist

.PHONY: all caselist

run: _inputPaths.yml
	./pyppl setup
	$(RUN)

%: _inputPaths.yml
	./pyppl setup
	$(RUN) $*

%-bsub4: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 4 $(RUN) $*
%-bsub8: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 8 $(RUN) $*
%-bsub16: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 16 $(RUN) $*

caselist: caselist.txt
	while read subj; do make $$subj-bsub8; done < caselist.txt

caselist.txt:
	$(error First make a caselist.txt with your subject ids, then run again)


##############################################################################
# Pipeline Setup
#
#  make software
#  make paths

.PHONY: software paths

software:
	./pyppl setup

paths: _inputPaths.yml

_inputPaths.yml:
ifeq ($(fromdir),)
	@echo \'fromdir\' not set, so create new $@ using makepathyml.py\'s ncurses interface
	./pnlscripts/makepathsyml.py -o $@ ncurses
else
	./pnlscripts/makepathsyml.py -o $@ fromdir $(fromdir)
endif


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

############################################################
# Make a shell script that adds BRAINSTools, pnlscripts, and
# tract_querier to $PATH and $PYTHONPATH
#
#  make env     # or
#  make _env.sh

.PHONY: env

BTHASH=41353e8
TQHASH=e045eab
BRAINSTOOLS=$(soft)/BRAINSTools-bin-$(BTHASH)
TRACT_QUERIER=$(soft)/tract_querier-$(TQHASH)

env: _env.sh
_env.sh:
	sed "s,__BRAINSTOOLS__,$(dir $(BRAINSTOOLS))," ._env.sh > $@
	sed -i "s,__TRACT_QUERIER__,$(dir $(TRACT_QUERIER))," $@
	@echo "Made '_env.sh'"
	@echo "Now run 'source _env.sh' to add pnlscripts, BRAINSTools, tract_querier, \
and the paths in _inputPaths.yml to your environment"

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
