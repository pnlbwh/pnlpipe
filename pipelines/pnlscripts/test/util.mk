%-bsub24: ; ../bsub-bigmulti.py -J $* -n 24 "make $*"
%-bsub16: ; ../bsub-bigmulti.py -J $* -n 16 "make $*"
%-bsub8: ; ../bsub-bigmulti.py -J $* -n 8 "make $*"
%-bsub4: ; ../bsub-bigmulti.py -J $* -n 4 "make $*"
%-bsub2: ; bsub -J $* -n 2 -q normal "make $*"
%-bsub1: ; bsub -J $* -n 1 -q normal "make $*"

print-%  : ; @echo $* = $($*)

define setup
	@mkdir -p $(@D)
	rm -rf $@
	$(call check_defined, $1 $2 $3 $4 $5)
endef

# Check that given variables are set and all have non-empty values,
# die with an error otherwise.
# Params:
#   1. Variable name(s) to test.
#   2. (optional) Error message to print.
check_defined = \
    $(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
    $(if $(value $1),, \
      $(error Undefined $1$(if $2, ($2))))
