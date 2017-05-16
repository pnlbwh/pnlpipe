include util.mk

extra1="--useIdentityMeaseurementFrame"
extra2="--useIdentityMeaseurementFrame --useBMatrixGradientDirections"

.PHONY: all
all: _data/dwi.nrrd _data/dwi.nii.gz _data/dwi-extraswitches1.nrrd _data/dwi-extraswitches2.nrrd

_data/dwi.nrrd: ../dwiconvert.py $(dwi)
	$(call setup, dwi)
	../dwiconvert.py -i $(dwi) -o /tmp/dwi.nii.gz
	../dwiconvert.py -i /tmp/dwi.nii.gz -o $@

_data/dwi-extraswitches1.nrrd: ../dwiconvert.py $(dwi)
	$(call setup, dwi)
	../dwiconvert.py -i $(dwi) --switches $(extra1) -o /tmp/dwi.nii.gz
	../dwiconvert.py -i /tmp/dwi.nii.gz --switches $(extra1) -o $@

_data/dwi-extraswitches2.nrrd: ../dwiconvert.py $(dwi)
	$(call setup, dwi)
	../dwiconvert.py -i $(dwi) --switches $(extra2) -o /tmp/dwi.nii.gz
	../dwiconvert.py -i /tmp/dwi.nii.gz --switches $(extra2) -o $@
