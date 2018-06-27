.PHONY: conda virtualenv nix

virtualenv: _venv
nix: _pip_packages.nix
conda: environment.yml
	@echo "Adding conda-forge to default conda channels"
	conda config --add channels conda-forge	
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
