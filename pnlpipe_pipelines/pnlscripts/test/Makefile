.PHONY: all clean
TARGETS := alignAndCenter atlas bse eddy epi fs2dwi fs wmql tractmeasures
.PHONY: $(TARGETS)

all: alignAndCenter atlas bse eddy epi fs2dwi fs wmql tractmeasures

clean: ; rm -rf *.err *.out

$(TARGETS):
	$(MAKE) -f $@.mk

# TODO add convertdwi test
# TODO add makeRigidMask test
