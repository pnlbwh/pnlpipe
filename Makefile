ifeq ($(PNLPIPE_SOFT),)
  $(error Export 'PNLPIPE_SOFT' first (This is where e.g. BRAINSTools and training data are/will be installed))
endif

PIPE := hcp
CASELIST := caselist.txt
PARAMS := params.$(PIPE)

# Run pipeline
# E.g. make
.PHONY: all clean pyclean bclean
all:
	./pnlpipe $(PIPE) run

clean:
	@echo "Not implemented yet (did you mean bclean?)"

pyclean:
	find . -name "*.pyc" -exec rm {} \;

.PHONY: bclean
bclean:
	rm *.err *.out

# Run pipeline for given subject id, overrides caseid field in params.<pnlpipe>
# file for each parameter combo.
# E.g. make 001
%:
	./pnlpipe $(PIPE) run $*

# Run pipeline using lsf
# E.g. make bsub8
bsub16: ; bsub -J "$(PIPE)" -o "%J.out" -e "%J.err" -q "big-multi" -n 16 ./pnlpipe $(PIPE) run
bsub8: ; bsub -J "$(PIPE)" -o "%J.out" -e "%J.err" -q "big-multi" -n 8 ./pnlpipe $(PIPE) run
bsub4: ; bsub -J "$(PIPE)" -o "%J.out" -e "%J.err" -q "big-multi" -n 4 ./pnlpipe $(PIPE) run

# Run pipeline for given subject id using lsf
# E.g. make 001-bsub8
%-bsub4: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 4 ./pnlpipe $(PIPE) run $*
%-bsub8: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 8 ./pnlpipe $(PIPE) run $*
%-bsub16: ; bsub -J $* -o "$*-%J.out" -e "$*-%J.err" -q "big-multi" -n 16 ./pnlpipe $(PIPE) run $*

.PHONY: caselist caselist-bsub8 caselist-bsub4
caselist: $(CASELIST)
	make caselist-bsub8

caselist-bsub8: $(CASELIST)
	cat caselist.txt | grep -Ev '^#' | while read subj; do if ! bjobs | grep $$subj >/dev/null; then make $$subj-bsub8; fi; done

caselist-bsub4: $(CASELIST)
	cat caselist.txt | grep -Ev '^#' | while read subj; do make $$subj-bsub4; done

$(CASELIST):
	$(error First make $(CASELIST) with your subject ids, then run again)
