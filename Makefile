.PHONY: clean conda env nix caselist software ukftractography
clean: ; rm -rf _env _requirements _environment.yml
env: _env
nix: _pip_packages.nix

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

software:
	$(call check_defined, soft, "Export 'soft' first e.g. export soft=/path/to/software")
	./pnlscripts/software.py --commit 41353e8 brainstools
	./pnlscripts/software.py --commit a8e354e tractquerier
	./pnlscripts/software.py trainingt1s
	./pnlscripts/software.py --commit 999f14d ukftractography

ukftractography:
	$(call check_defined, soft, "Export 'soft' first e.g. export soft=/path/to/software")
	./pnlscripts/software.py --commit 999f14d ukftractography

%-bsub4:
	bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 4 ./pnlrun $*
%-bsub8:
	bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 8 ./pnlrun $*
%-bsub16:
	bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 16 ./pnlrun $*
caselist:
	while read subj; do echo $$subj-bsub8; done < caselist.txt


# Params:
#   1. Variable name(s) to test.
#   2. (optional) Error message to print.
check_defined = \
    $(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
    $(if $(value $1),, \
      $(error Undefined $1$(if $2, ($2))))
