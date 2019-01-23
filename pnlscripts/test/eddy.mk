include util.mk

all: _data/dwied.nrrd

_data/dwied.nrrd: ../eddy.py $(dwi)
	$(call setup, dwi)
	../eddy.py -i $(dwi) -o $@
