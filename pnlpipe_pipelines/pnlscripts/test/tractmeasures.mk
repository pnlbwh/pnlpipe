include util.mk

.PHONY: all
all: _data/tractmeasures.csv

_data/tractmeasures.csv: ../measuretracts/measureTracts.py $(wmqltracts)
	$(call setup, wmqltracts)
	../measuretracts/measureTracts.py -f -c "caseid" "algo" -v case001 pnlalgo -o $@ -i $(wmqltracts)/*.vtk
