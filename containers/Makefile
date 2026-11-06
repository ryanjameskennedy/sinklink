# Downloads the Singularity/Apptainer images used by this repository, in the
# same way as the JASEN containers Makefile. URLs and versions match JASEN, so
# a JASEN containers folder can be reused as CONTAINERS_DIR.
#
#   make all CONTAINERS_DIR=/mnt/cache/singularity
SHELL := /bin/bash

SRC_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
CONTAINERS_DIR ?= $(SRC_DIR)
override CONTAINERS_DIR := $(abspath $(CONTAINERS_DIR))
INSTALL_LOG := $(CONTAINERS_DIR)/.install.log
APPTAINER ?= apptainer

all: build_local_containers \
	download_remote_containers

# Built from Docker images, as these are not on the Galaxy depot
local_containers := gambitcore.sif \
					medaka.sif

remote_containers := bracken.sif \
					bwakit.sif \
					chewbbaca.sif \
					fastqc.sif \
					filtlong.sif \
					flye.sif \
					kraken2.sif \
					minimap2.sif \
					mlst.sif \
					nanoplot.sif \
					prodigal.sif \
					quast.sif \
					samtools.sif \
					skesa.sif \
					spades.sif \
					trimmomatic.sif

local_container_sifs := $(addprefix $(CONTAINERS_DIR)/,$(local_containers))
remote_container_sifs := $(addprefix $(CONTAINERS_DIR)/,$(remote_containers))

DOCKER_gambitcore := docker://clinicalgenomicslund/gambitcore:0.0.2
DOCKER_medaka := docker://ontresearch/medaka:shacf8338462607b17b1d68dbce212cb93daea50bad

URL_bracken := https://depot.galaxyproject.org/singularity/bracken:2.8--py39hc16433a_0
URL_bwakit := https://depot.galaxyproject.org/singularity/bwakit:0.7.17.dev1--hdfd78af_1
URL_chewbbaca := https://depot.galaxyproject.org/singularity/chewbbaca:3.5.4--pyh106432d_0
URL_fastqc := https://depot.galaxyproject.org/singularity/fastqc:0.12.1--hdfd78af_0
URL_filtlong := https://depot.galaxyproject.org/singularity/filtlong:0.3.1--h077b44d_0
URL_flye := https://depot.galaxyproject.org/singularity/flye:2.9.6--py39h475c85d_0
URL_kraken2 := https://depot.galaxyproject.org/singularity/mulled-v2-f8c4015c836dd3ce5c118cfed97ec8259bab9e9d:41404a18634d1ec6fe2a8a0dc54df6925d57fdbf-0
URL_minimap2 := https://depot.galaxyproject.org/singularity/minimap2:2.30--h577a1d6_0
URL_mlst := https://depot.galaxyproject.org/singularity/mlst:2.23.0--hdfd78af_1
URL_nanoplot := https://depot.galaxyproject.org/singularity/nanoplot:1.46.2--pyhdfd78af_0
URL_prodigal := https://depot.galaxyproject.org/singularity/prodigal:2.6.3--h7b50bb2_10
URL_quast := https://depot.galaxyproject.org/singularity/quast:5.2.0--py310pl5321hc8f18ef_2
URL_samtools := https://depot.galaxyproject.org/singularity/samtools:1.17--h00cdaf9_0
URL_skesa := https://depot.galaxyproject.org/singularity/skesa:2.5.1--hdcf5f25_0
URL_spades := https://depot.galaxyproject.org/singularity/spades:3.15.5--h95f258a_1
URL_trimmomatic := https://depot.galaxyproject.org/singularity/trimmomatic:0.40--hdfd78af_0

define log_message
	@echo "--------------------------------------------------------------------------------" | tee -a $(INSTALL_LOG);
	@echo "$$(date "+%Y-%m-%d %H:%M:%S"): $1" | tee -a $(INSTALL_LOG);
	@echo "--------------------------------------------------------------------------------" | tee -a $(INSTALL_LOG);
endef

.PHONY: all build_local_containers download_remote_containers \
	print_local_containers print_remote_containers

print_local_containers:
	@for cont in $(local_containers); do echo $$cont; done

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

build_local_containers: $(local_container_sifs)

$(local_container_sifs): | $(INSTALL_LOG)
	$(call log_message,"Building local container $(notdir $@) ...")
	$(eval tool := $(basename $(notdir $@)))
	$(eval container_url := ${DOCKER_${tool}})
	@mkdir -p $(CONTAINERS_DIR) \
	&& cd $(CONTAINERS_DIR) \
	&& output_file=$$(echo ${container_url} | sed -e 's#docker://##' -e 's#/#-#g' -e 's#:#-#g').img \
	&& $(APPTAINER) build --force $${output_file} ${container_url} \
	&& ln -sf $${output_file} $(notdir $@)

$(INSTALL_LOG):
	@mkdir -p $(dir $@) && touch $@
