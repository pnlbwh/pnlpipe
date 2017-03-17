ifeq ($(soft),)
  $(error Export 'soft' first (This is where e.g. BRAINSTools and training data are/will be installed))
endif

PIPE := std
CASELIST := caselist.txt
PARAMS := params.$(PIPE)

# Run pipeline
# E.g. make
.PHONY: all
all:
	./pipe $(PIPE) run

# Run pipeline for given subject id
# E.g. make 001
%:
	./pipe $(PIPE) run --subjid $*

# Run pipeline using lsf
# E.g. make bsub8
bsub16: ; bsub -J "$(PIPE)" -o "%J.out" -e "%J.err" -q "big-multi" -n 16 ./pipe $(PIPE) run
bsub8: ; bsub -J "$(PIPE)" -o "%J.out" -e "%J.err" -q "big-multi" -n 8 ./pipe $(PIPE) run
bsub4: ; bsub -J "$(PIPE)" -o "%J.out" -e "%J.err" -q "big-multi" -n 4 ./pipe $(PIPE) run

# Run pipeline for given subject id using lsf
# E.g. make 001-bsub8
%-bsub4: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 4 ./pipe $(PIPE) run --subjid $*
%-bsub8: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 8 ./pipe $(PIPE) run --subjid $*
%-bsub16: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 16 ./pipe $(PIPE) run --subjid $*

caselist-bsub8: $(CASELIST)
	while read subj; do make $$subj-bsub8; done < caselist.txt

caselist-bsub4: $(CASELIST)
	while read subj; do make $$subj-bsub4; done < caselist.txt

$(CASELIST):
	$(error First make $(CASELIST) with your subject ids, then run again)

##############################################################################
# Python Environments

.PHONY: conda virtualenv nix

virutalenv: _venv
nix: _pip_packages.nix
conda: environment.yml
	conda env create -f $<
	@echo "Now run 'source activate pnlpipe'"

_venv: requirements.txt
	virtualenv $@; $@/bin/pip install -r $<
	@echo "Now run 'source $@/bin/activate'"

_pip_packages.nix: requirements.txt
	if [ ! -d "_pip2nix" ]; then \
		git clone https://github.com/acowley/pip2nix _pip2nix; \
  fi
	cd _pip2nix; nix-shell --run 'pip2nix ../requirements.txt -o ../_pip_packages.nix'
	@echo "Now run 'nix-shell'"
