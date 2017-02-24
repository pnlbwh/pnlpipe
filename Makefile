.PHONY: all clean nix conda env
clean: ; rm pip_packages.nix
nix: pip_packages.nix
env: _pnlscripts-env

pip_packages.nix: requirements.txt
	if [ ! -d "_pip2nix" ]; then \
		git clone https://github.com/acowley/pip2nix _pip2nix; \
  fi
	cd _pip2nix; nix-shell --run 'pip2nix ../requirements.txt -o ../pip_packages.nix'
	@echo "Now run 'nix-shell'"

conda: environment.yml
	conda env create -f $<
	@echo "Now run `source activate pnlscripts`"

_pnlscripts-env: requirements.txt
	virtualenv $@; $@/bin/pip install -r $<
	@echo "Now run `source $@/bin/activate`"
