ifeq ($(soft),)
  $(error Export 'soft' first (This is where e.g. BRAINSTools and training data are/will be installed))
endif

CASELIST := caselist.txt
SUBCMD := std run
PARAMS := params.std

.PHONY: all
all: inputPaths.yml $(PARAMS)
	./pipe $(SUBCMD)

%-bsub4: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 4 ./pipe --subjid $* $(SUBCMD) $*
%-bsub8: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 8 ./pipe --subjid $* $(SUBCMD) $*
%-bsub16: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 16 ./pipe --subjid $* $(SUBCMD) $*

caselist: $(CASELIST)
	while read subj; do make $$subj-bsub8; done < caselist.txt

$(CASELIST):
	$(error First make $(CASELIST) with your subject ids, then run again)

##############################################################################
# Python Environments

.PHONY: conda env nix

venv: _venv
nix: _pip_packages.nix
conda: _environment.yml
	conda env create -f $<
	@echo "Now run `source activate pyppl`"

_venv: requirements.txt
	virtualenv $@; $@/bin/pip install -r $<
	@echo "Now run `source $@/bin/activate`"

_pip_packages.nix: requirements.txt
	if [ ! -d "_pip2nix" ]; then \
		git clone https://github.com/acowley/pip2nix _pip2nix; \
  fi
	cd _pip2nix; nix-shell --run 'pip2nix ../requirements.txt -o ../_pip_packages.nix'
	@echo "Now run 'nix-shell'"
