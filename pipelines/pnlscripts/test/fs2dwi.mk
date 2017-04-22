include util.mk

.PHONY: all
all: _data/fs2dwi

_data/fs2dwi: ../fs2dwi.py $(fs) $(dwi) $(dwimask)
	$(call setup, fs dwi dwimask)
	../fs2dwi.py -f $(fs) -t $(dwi) -m $(dwimask) -o $@ direct
