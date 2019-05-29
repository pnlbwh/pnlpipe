.PHONY: conda virtualenv

virtualenv: _venv
conda: environment36.yml
	@echo "Adding conda-forge to default conda channels"
	conda config --add channels conda-forge	
	conda env create -f $<

_venv: requirements.txt
	virtualenv $@; $@/bin/pip install -r $<
	@echo "Now run 'source $@/bin/activate'"

