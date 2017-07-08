include util.mk

.PHONY: all
all: _data/dwiepi.nrrd

_data/dwiepi.nrrd: ../epi.py $(dwi) $(dwimask) $(t2) $(t2mask)
	$(call setup, dwi dwimask t2 t2mask)
	rm -rf _data/epidebug-*
	rm -rf $@
	../epi.py -d --dwi $(dwi) --dwimask $(dwimask) --t2 $(t2) --t2mask $(t2mask) --out $@
