.PHONY: clean conda env
clean: ; rm -rf _env _requirements _environment.yml
env: _env

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
