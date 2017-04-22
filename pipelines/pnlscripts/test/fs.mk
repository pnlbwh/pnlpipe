include util.mk

.PHONY: all
all: _data/fs-withmask/mri/wmparc.mgz _data/fs-withskullstrip/mri/wmparc.mgz

_data/fs-withskullstrip/mri/wmparc.mgz: ../fs.py $(t1)
	$(call setup, t1)
	../fs.py -i $(t1) -f -o _data/fs-withskullstrip

_data/fs-withmask/mri/wmparc.mgz: ../fs.py $(t1) $(t1mask)
	$(call setup, t1 t1mask)
	../fs.py -i $(t1) -m $(t1mask) -f -o _data/fs-withmask
