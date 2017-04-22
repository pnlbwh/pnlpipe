include util.mk

.PHONY: all
all: _data/wmql

_data/wmql: ../wmql.py $(ukf) $(fsindwi)
	$(call setup, ukf fsindwi)
	../wmql.py -i $(ukf) -f $(fsindwi) --query ../wmql-2.0.qry -o $@
