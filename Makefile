ifeq ($(soft),)
  $(error Export 'soft' first (This is where e.g. BRAINSTools and training data are/will be installed))
endif

.PHONY: all clean conda env nix
all: _paths.yml
	./pyppl
env: _env
nix: _pip_packages.nix

BTHASH=41353e8
TQHASH=a8e354e
UKFHASH=999f14d

##############################################################################
# Setup Python Environment

conda: _environment.yml
	conda env create -f $<
	@echo "Now run `source activate pyppl`"

_env: _requirements.txt
	virtualenv $@; $@/bin/pip install -r $<
	@echo "Now run `source $@/bin/activate`"

_environment.yml: pnlscripts/environment.yml
	cp $< $@
	echo '  - pyyaml' >> $@
	echo '  - python_log_indenter' >> $@
	sed -i 's/pnlscripts/pyppl/' $@

_requirements.txt: pnlscripts/requirements.txt
	cp $< $@
	echo 'pyyaml' >> $@
	echo 'python_log_indenter' >> $@

_pip_packages.nix: _requirements.txt
	if [ ! -d "_pip2nix" ]; then \
		git clone https://github.com/acowley/pip2nix _pip2nix; \
  fi
	cd _pip2nix; nix-shell --run 'pip2nix ../_requirements.txt -o ../_pip_packages.nix'
	@echo "Now run 'nix-shell'"

##############################################################################
# Setup Pipeline Software

software:
	./pnlscripts/software.py --commit $(BTHASH) brainstools
	./pnlscripts/software.py --commit $(TQHASH) tractquerier
	./pnlscripts/software.py trainingt1s
	./pnlscripts/software.py --commit $(UKFHASH) ukftractography

ukftractography:
	./pnlscripts/software.py --commit $(UKFHASH) ukftractography


##############################################################################
# Run pipeline

.PHONY: paths
paths: _paths.yml
_paths.yml:
ifeq ($(dir),)
	./pnlscripts/makepathsyml.py -o $@
else
	./pnlscripts/makepathsyml.py -o $@ fromdir $(dir)
endif
%-bsub4:
	bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 4 ./pyppl $*
%-bsub8:
	bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 8 ./pyppl $*
%-bsub16:
	bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 16 ./pyppl $*
caselist: caselist.txt
	while read subj; do echo $$subj-bsub8; done < caselist.txt
caselist.txt:
	$(error First make a caselist.txt with your subject ids, then run again)


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
