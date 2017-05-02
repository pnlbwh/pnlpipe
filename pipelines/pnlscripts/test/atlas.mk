include util.mk

ifeq ($(soft),)
  $(error Export 'soft' first (This is where training data is installed))
endif

T2_CASEIDS=01063 01099
T2_PREFIXES=$(addprefix $(soft)/trainingDataT2Masks/, $(T2_CASEIDS))
T2S=$(addsuffix -t2w.nrrd, $(T2_PREFIXES))
T2_MASKS=$(addsuffix -t2w-mask.nrrd, $(T2_PREFIXES))

T1_CASEIDS=006_ACT_002 006_TRM_007
T1_PREFIXES=$(addprefix $(soft)/trainingDataT1AHCC/, $(T1_CASEIDS))
T1S=$(addsuffix -t1w-realign.cent.nrrd, $(T1_PREFIXES))
T1_MASKS=$(addsuffix -t1w-realign-mask.nrrd, $(T1_PREFIXES))
T1_CINGRS=$(addsuffix -AHCC-cingr.nrrd, $(T1_PREFIXES))

.PHONY: all t2atlas t1atlas t1atlascsv
all: t2atlas t1atlas t1atlascsv

t2atlas: $(addprefix _data/t2atlas/, mask0.nrrd mask1.nrrd)
t1atlas: $(addprefix _data/t1atlas/, mask0.nrrd mask1.nrrd cingr0.nrrd cingr1.nrrd)
t1atlascsv: $(addprefix _data/t1atlascsv/, mask0.nrrd mask1.nrrd)

_data/t2atlas/%0.nrrd _data/t2atlas/%1.nrrd _data/t2atlas/%.nrrd: ../atlas.py $(T2S) $(T2_MASKS)
	$(call setup, t2)
	../atlas.py args --fusion antsJointFusion -t $(t2) -o $(dir $@) -i "$(T2S)" -l "$(T2_MASKS)" -n mask

_data/t1atlas/%0.nrrd _data/t1atlas/%1.nrrd _data/t1atlas/%.nrrd: ../atlas.py $(T1S) $(T1_MASKS) $(T1_CINGRS)
	$(call setup, t1)
	../atlas.py args --fusion avg -t $(t1) -o $(dir $@) -i "$(T1S)" -l "$(T1_MASKS) $(T1_CINGRS)" -n "mask cingr"

_data/t1atlascsv/%0.nrrd _data/t1atlascsv/%1.nrrd _data/t1atlascsv/%.nrrd: ../atlas.py $(T1S) $(T1_MASKS) $(T1_CINGRS)
	$(call setup, t1)
	../atlas.py csv --fusion avg -t $(t1) -o $(dir $@) $(soft)/trainingDataT1AHCC/trainingDataT1AHCC-hdr.csv
