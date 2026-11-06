# Downloads the Singularity/Apptainer images used by this repository, in the
# same way as the JASEN containers Makefile.
#
#   make all CONTAINERS_DIR=/mnt/cache/singularity
SHELL := /bin/bash

SRC_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
CONTAINERS_DIR ?= $(SRC_DIR)
override CONTAINERS_DIR := $(abspath $(CONTAINERS_DIR))
INSTALL_LOG := $(CONTAINERS_DIR)/.install.log

all: download_remote_containers

remote_containers := chewbbaca.sif \
					prodigal.sif

remote_container_sifs := $(addprefix $(CONTAINERS_DIR)/,$(remote_containers))

URL_chewbbaca := https://depot.galaxyproject.org/singularity/chewbbaca:3.5.4--pyh106432d_0
URL_prodigal := https://depot.galaxyproject.org/singularity/prodigal:2.6.3--h7b50bb2_10

define log_message
	@echo "--------------------------------------------------------------------------------" | tee -a $(INSTALL_LOG);
	@echo "$$(date "+%Y-%m-%d %H:%M:%S"): $1" | tee -a $(INSTALL_LOG);
	@echo "--------------------------------------------------------------------------------" | tee -a $(INSTALL_LOG);
endef

.PHONY: all download_remote_containers print_remote_containers

print_remote_containers:
	@for cont in $(remote_containers); do echo $$cont; done

download_remote_containers: $(remote_container_sifs)

$(remote_container_sifs): | $(INSTALL_LOG)
	$(call log_message,"Downloading remote container $(notdir $@) ...")
	$(eval tool := $(basename $(notdir $@)))
	$(eval container_url := ${URL_${tool}})
	$(eval sanitized_url := $(shell echo ${container_url} | sed -e 's/%3A/:/g'))
	@mkdir -p $(CONTAINERS_DIR) \
	&& cd $(CONTAINERS_DIR) \
	&& output_file=$$(echo ${sanitized_url} | sed -e 's#https://##' -e 's#/#-#g' -e 's#:#-#g').img \
	&& wget -O $${output_file} ${sanitized_url} --no-check-certificate \
	&& ln -sf $${output_file} $(notdir $@)

$(INSTALL_LOG):
	@mkdir -p $(dir $@) && touch $@
