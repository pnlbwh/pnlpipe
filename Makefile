ifeq ($(soft),)
  $(error Export 'soft' first (This is where e.g. BRAINSTools and training data are/will be installed))
endif

.PHONY: all
all: _paths.yml
ifeq ($(want),)
	./pyppl
else
	./pyppl --want $(want)
endif

##############################################################################
# Setup Python Environment

.PHONY: clean conda env nix

env: _env

nix: _pip_packages.nix
	@echo "now run 'nix-shell'"

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

BTHASH=41353e8
TQHASH=a8e354e
UKFHASH=999f14d

ukf=$(soft)/UKFTractography-$(UKFHASH)
bt=$(soft)/BRAINSTools-bin-$(BTHASH)/antsRegistration
tq=$(soft)/tract_querier-$(TQHASH)/README.md
t1s=$(soft)/trainingDataT1AHCC/trainingDataT1AHCC-hdr.csv

.PHONY: software
software: $(tq) $(t1s) $(bt) $(ukf)

$(ukf): ; ./pnlscripts/software.py --commit $(UKFHASH) ukftractography
$(bt): ; ./pnlscripts/software.py --commit $(BTHASH) brainstools
$(tq): ; ./pnlscripts/software.py --commit $(TQHASH) tractquerier
$(t1s): ; ./pnlscripts/software.py trainingt1s


##############################################################################
# Run pipeline

.PHONY: run
run: _paths.yml $(ukf) $(tq) $(bt) $(ukf)
ifeq ($(want),)
	./pyppl
else
	./pyppl --want $(want)
endif

.PHONY: paths
paths: _paths.yml

_paths.yml:
ifeq ($(fromdir),)
	./pnlscripts/makepathsyml.py -o $@
else
	./pnlscripts/makepathsyml.py -o $@ fromdir $(fromdir)
endif

%-bsub4: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 4 ./pyppl $*
%-bsub8: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 8 ./pyppl $*
%-bsub16: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 16 ./pyppl $*

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
