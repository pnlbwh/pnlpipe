include util.mk

.PHONY: all
all: _data/b0.nrrd _data/b0.nii.gz _data/b0masked.nrrd

_data/b0.nrrd: ../bse.py $(dwi)
	$(call setup, dwi)
	../bse.py -i $(dwi) -o $@

_data/b0.nii.gz: ../bse.py ../dwiconvert.py $(dwi)
	$(call setup, dwi)
	../dwiconvert.py -i $(dwi) -o _data/dwi.nii.gz
	../bse.py -i _data/dwi.nii.gz -o $@

_data/b0masked.nrrd: ../bse.py $(dwi) $(dwimask)
	$(call setup, dwi dwimask)
	../bse.py -m $(dwimask) -i $(dwi) -o $@
