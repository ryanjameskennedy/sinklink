# Downloads the Singularity images used by the setup in the top-level
# Makefile (chewBBACA PrepExternalSchema, Prodigal training, reference genome
# download with jasentool and indexing with samtools), in the same way as the
# JASEN containers Makefile.
#
# Each image is saved under the file name Nextflow gives it in its Singularity
# cache (the URL without https://, with / and : replaced by -). chewBBACA and
# samtools are the same images the pipeline uses, so when CONTAINERS_DIR is the
# pipeline's Singularity/Apptainer cacheDir the pipeline reuses them instead of pulling
# them again. The pipeline pulls its other containers itself on the first run.
#
#   make all CONTAINERS_DIR=/mnt/cache/singularity
SHELL := /bin/bash

SRC_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
CONTAINERS_DIR ?= $(SRC_DIR)
override CONTAINERS_DIR := $(abspath $(CONTAINERS_DIR))
INSTALL_LOG := $(CONTAINERS_DIR)/.install.log

all: download_remote_containers build_local_containers

remote_containers := chewbbaca.sif \
					prodigal.sif \
					samtools.sif

local_containers := jasentool.sif

remote_container_sifs := $(addprefix $(CONTAINERS_DIR)/,$(remote_containers))
local_container_sifs := $(addprefix $(CONTAINERS_DIR)/,$(local_containers))

URL_chewbbaca := https://depot.galaxyproject.org/singularity/chewbbaca:3.5.4--pyh106432d_0
URL_prodigal := https://depot.galaxyproject.org/singularity/prodigal:2.6.3--h7b50bb2_10
URL_samtools := https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/e9/e994bf4eb3731150511a14f5706b7bdfd64df1b6d40898fff334286c027e0859/data

DOCKER_jasentool := docker://clinicalgenomicslund/jasentool:1.3.0

define log_message
	@echo "--------------------------------------------------------------------------------" | tee -a $(INSTALL_LOG);
	@echo "$$(date "+%Y-%m-%d %H:%M:%S"): $1" | tee -a $(INSTALL_LOG);
	@echo "--------------------------------------------------------------------------------" | tee -a $(INSTALL_LOG);
endef

.PHONY: all download_remote_containers build_local_containers print_remote_containers

print_remote_containers:
	@for cont in $(remote_containers); do echo $$cont; done

download_remote_containers: $(remote_container_sifs)

build_local_containers: $(local_container_sifs)

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

$(local_container_sifs): | $(INSTALL_LOG)
	$(call log_message,"Building local container $(notdir $@) ...")
	$(eval tool := $(basename $(notdir $@)))
	$(eval container_url := ${DOCKER_${tool}})
	@mkdir -p $(CONTAINERS_DIR) \
	&& cd $(CONTAINERS_DIR) \
	&& output_file=$$(echo ${container_url} | sed -e 's#docker://##' -e 's#/#-#g' -e 's#:#-#g').img \
	&& singularity build --force $${output_file} ${container_url} \
	&& ln -sf $${output_file} $(notdir $@)

$(INSTALL_LOG):
	@mkdir -p $(dir $@) && touch $@
