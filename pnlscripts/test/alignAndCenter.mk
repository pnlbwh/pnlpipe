include util.mk

all: _data/xcFromNrrd.nrrd

_data/xcFromNrrd.nrrd: ../alignAndCenter.py ../center.py ../axisAlign.py $(t1)
	$(call setup, t1)
	../alignAndCenter.py -i $(t1) -o $@
