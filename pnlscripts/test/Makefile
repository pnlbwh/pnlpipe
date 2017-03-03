T2_CASEIDS=01063 01099
T2_PREFIXES=$(addprefix $(soft)/trainingDataT2Masks/, $(T2_CASEIDS))
T2S=$(addsuffix -t2w.nrrd, $(T2_PREFIXES))
T2_MASKS=$(addsuffix -t2w-mask.nrrd, $(T2_PREFIXES))

T1_CASEIDS=006_ACT_002 006_TRM_007
T1_PREFIXES=$(addprefix $(soft)/trainingDataT1AHCC/, $(T1_CASEIDS))
T1S=$(addsuffix -t1w-realign.cent.nrrd, $(T1_PREFIXES))
T1_MASKS=$(addsuffix -t1w-realign-mask.nrrd, $(T1_PREFIXES))
T1_CINGRS=$(addsuffix -AHCC-cingr.nrrd, $(T1_PREFIXES))

.PHONY: all clean epi b0 b0masked ed t2atlas t1atlas fs fs2dwi wmql xc
all: xc b0 b0masked ed  epi fs fsx fs2dwi t2atlas t1atlas t1atlascsv wmql tractmeasures
xc: _data/xcFromNii.nrrd _data/xcFromNrrd.nrrd
b0: _data/b0.nrrd
b0masked: _data/b0masked.nrrd
ed: _data/dwied.nrrd
epi: _data/dwiepi.nrrd
fs: _data/fs-withmask/mri/wmparc.mgz
fsx: _data/fs-withskullstrip/mri/wmparc.mgz
fs2dwi: _data/fs2dwi
t2atlas: $(addprefix _data/t2atlas/, mask0.nrrd mask1.nrrd)
t1atlas: $(addprefix _data/t1atlas/, mask0.nrrd mask1.nrrd)
t1atlascsv: $(addprefix _data/t1atlascsv/, mask0.nrrd mask1.nrrd)
wmql: _data/wmql
tractmeasures: _data/tractmeasures.csv

clean: ; rm -rf *.err *.out

# TODO add convertdwi test
# TODO add makeRigidMask test

_data/xcFromNii.nrrd: ../alignAndCenter.py ../center.py ../axisalign.py
	$(call setup, t1)
	ConvertBetweenFileFormats $(t1) /tmp/t1.nii.gz
	../alignAndCenter.py -i /tmp/t1.nii.gz -o $@

_data/xcFromNrrd.nrrd: ../alignAndCenter.py ../center.py ../axisalign.py
	$(call setup, t1)
	../alignAndCenter.py -i $(t1) -o $@

_data/b0masked.nrrd: ../bse.py
	$(call setup, dwi dwimask)
	../bse.py -m $(dwimask) -i $(dwi) -o $@

_data/b0.nrrd: ../bse.py
	$(call setup, dwi)
	../bse.py -i $(dwi) -o $@

_data/dwied.nrrd: ../eddy.py
	$(call setup, dwi)
	../eddy.py -i $(dwi) -o $@

_data/dwiepi.nrrd: ../epi.py
	$(call setup, dwi dwimask t2 t2mask)
	rm -rf _data/epidebug-*
	rm -rf $@
	../epi.py -d --dwi $(dwi) --dwimask $(dwimask) --t2 $(t2) --t2mask $(t2mask) --out $@

_data/t2atlas/%0.nrr _data/t2atlas/%1.nrrd _data/t2atlas/%.nrrd: ../atlas.py $(T2S) $(T2_MASKS)
	$(call setup, t2)
	../atlas.py --mabs -t $(t2) -o $(dir $@) args -g "$(T2S)" -l "$(T2_MASKS)" -n mask

_data/t1atlas/%0.nrrd _data/t1atlas/%1.nrrd _data/t1atlas/%.nrrd: ../atlas.py $(T1S) $(T1_MASKS) $(T1_CINGRS)
	$(call setup, t1)
	../atlas.py --mabs -t $(t1) -o $(dir $@) args -g "$(T1S)" -l "$(T1_MASKS) $(T1_CINGRS)" -n "mask cingr"

_data/t1atlascsv/%0.nrrd _data/t1atlascsv/%1.nrrd _data/t1atlascsv/%.nrrd: ../atlas.py $(T1S) $(T1_MASKS) $(T1_CINGRS)
	$(call setup, t1)
	../atlas.py --mabs -t $(t1) -o $@ csv $(soft)/trainingDataT1AHCC/trainingDataT1AHCC-hdr.csv

$(soft)/trainingDataT2Masks/%.nrrd $(soft)/trainingDataT2Masks/%-mask.nrrd:
	../software.py trainingt2s

$(soft)/trainingDataT1AHCC/%-t1w-realign-mask.nrrd $(soft)/trainingDataT1AHCC/%-AHCC-cingr.nrrd $(soft)/trainingDataT1AHCC/%-t1w-realign.cent.nrrd :
	../software.py trainingt1s

_data/fs2dwi: ../fs2dwi.py
	$(call setup, fs dwi dwimask)
	../fs2dwi.py -f $(fs) -t $(dwi) -m $(dwimask) -o $@ direct

_data/fs-withskullstrip/mri/wmparc.mgz: ../fs.py
	$(call setup, t1)
	../fs.py -i $(t1) -f -o _data/fs-withskullstrip

_data/fs-withmask/mri/wmparc.mgz: ../fs.py
	$(call setup, t1 t1mask)
	../fs.py -i $(t1) -m $(t1mask) -f -o _data/fs-withmask

_data/wmql: ../wmql.py
	$(call setup, ukf fsindwi)
	../wmql.py -i $(ukf) -f $(fsindwi) --query ../wmql-2.0.qry -o $@

_data/tractmeasures.csv:
	$(call setup, wmqltracts)
	../measuretracts/measureTracts.py -f -c "caseid" "algo" -v case001 pnlalgo -o $@ -i $(wmqltracts)/*.vtk

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
