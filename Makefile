# Sets up the chewBBACA schemas, reference genomes and databases used to compare
# isolates within each transmission group, following the layout of the JASEN
# Makefile.
#
#   make print_paths
#   make install ASSETS_DIR=/mnt/cache/dbs CONTAINERS_DIR=/mnt/cache/singularity
#
# Single organisms can be set up on their own, e.g. `make paeruginosa_all`.
# ==============================================================================
# Various definitions
# ==============================================================================
SHELL := /bin/bash

SCRIPT_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
ASSETS_DIR ?= $(SCRIPT_DIR)/assets
CONTAINERS_DIR ?= $(SCRIPT_DIR)/containers
override ASSETS_DIR := $(abspath $(ASSETS_DIR))
override CONTAINERS_DIR := $(abspath $(CONTAINERS_DIR))
CONTAINERS_SRC_DIR := $(SCRIPT_DIR)/containers
SCHEMAS_DIR := $(ASSETS_DIR)/schemas
GENOMES_DIR := $(ASSETS_DIR)/genomes
PRODIGAL_TRAINING_DIR := $(ASSETS_DIR)/prodigal_training_files
GAMBIT_DIR := $(ASSETS_DIR)/gambit_db
GAMBIT_URL := https://storage.googleapis.com/jlumpe-gambit/public/databases/refseq-curated/1.0
GAMBIT_FILES := gambit-refseq-curated-1.0.gdb gambit-refseq-curated-1.0.gs
REFERENCES_DIR := $(ASSETS_DIR)/references
REFERENCES := $(shell awk -F'\t' 'NR==1 {for (i = 1; i <= NF; i++) if ($$i == "reference") col = i; next} $$col != "" {print $$col}' $(SCRIPT_DIR)/assets/schemas.tsv)
NCBI_DATASETS := https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession
DEACON_DIR := $(ASSETS_DIR)/deacon
DEACON_INDEX := panhuman-1.k31w15.idx
DEACON_URL := https://objectstorage.uk-london-1.oraclecloud.com/n/lrbvkel2wjot/b/human-genome-bucket/o/deacon/3/$(DEACON_INDEX)

SINGULARITY ?= singularity
PREP_CPUS ?= 4
PYTHON ?= python3

mnt_root = /$(word 1,$(subst /, ,$(1)))
BIND_ROOTS := $(sort $(call mnt_root,$(SCRIPT_DIR)) $(call mnt_root,$(ASSETS_DIR)) $(call mnt_root,$(CONTAINERS_DIR)))
BIND_ARGS := $(foreach root,$(BIND_ROOTS),--bind $(root))
INSTALL_LOG := "$(SCRIPT_DIR)/.install.log"

define log_message
	@echo "--------------------------------------------------------------------------------" | tee -a $(INSTALL_LOG);
	@echo "$$(date "+%Y-%m-%d %H:%M:%S"): $1" | tee -a $(INSTALL_LOG);
	@echo "--------------------------------------------------------------------------------" | tee -a $(INSTALL_LOG);
endef

# ------------------------------------------------------------------------------
# Schemas. Each needs an allele download URL, the archive name to save it as and
# the seed (reference) genome used to train Prodigal for PrepExternalSchema.
# Thresholds used when checking distances live in assets/schemas.tsv.
# ------------------------------------------------------------------------------
SCHEMAS := paeruginosa \
	kpneumoniae \
	koxytoca \
	smarcescens \
	cfreundii \
	ehormaechei \
	smaltophilia

NAME_paeruginosa := P. aeruginosa
URL_paeruginosa := https://www.cgmlst.org/ncs/schema/Paeruginosa/alleles/
ARCHIVE_paeruginosa := alleles.zip
SEED_paeruginosa := NC_002516.2

NAME_kpneumoniae := K. pneumoniae sensu lato
URL_kpneumoniae := https://www.cgmlst.org/ncs/schema/Kpneumoniae_complex/alleles/
ARCHIVE_kpneumoniae := alleles.zip
SEED_kpneumoniae := NC_012731.1

NAME_koxytoca := K. oxytoca species complex
URL_koxytoca := https://www.cgmlst.org/ncs/schema/Koxytoca_complex/alleles/
ARCHIVE_koxytoca := alleles.zip
SEED_koxytoca := NZ_CP033844.1

NAME_smarcescens := S. marcescens
URL_smarcescens := https://www.cgmlst.org/ncs/schema/Smarcescens/alleles/
ARCHIVE_smarcescens := alleles.zip
SEED_smarcescens := NZ_HG326223.1

NAME_cfreundii := C. freundii
URL_cfreundii := https://www.cgmlst.org/ncs/schema/Cfreundii/alleles/
ARCHIVE_cfreundii := alleles.zip
SEED_cfreundii := NZ_CP049015.1

NAME_ehormaechei := E. hormaechei
URL_ehormaechei := https://www.cgmlst.org/ncs/schema/Ehormaechei/alleles/
ARCHIVE_ehormaechei := alleles.zip
SEED_ehormaechei := NZ_CP100388.1

# Groschel et al. 2020 wgMLST, published as a single FASTA of all alleles.
NAME_smaltophilia := S. maltophilia
URL_smaltophilia := https://figshare.com/ndownloader/files/18042350
ARCHIVE_smaltophilia := Smaltophilia_wgMLST_all-alleles.fasta.gz
SEED_smaltophilia := NC_010943.1
EXPECT_LOCI_smaltophilia := 17603

NCBI_EFETCH := https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&rettype=fasta&retmode=text

# ==============================================================================
# Main rules
# ==============================================================================
.PHONY: print_paths install download_or_build_containers schemas databases gambit_db \
	deacon_index references check check_schemas check_databases check_references

print_paths:
	@echo "SCRIPT_DIR:" $(SCRIPT_DIR)
	@echo "ASSETS_DIR:" $(ASSETS_DIR)
	@echo "CONTAINERS_DIR:" $(CONTAINERS_DIR)
	@echo "SCHEMAS_DIR:" $(SCHEMAS_DIR)
	@echo "GAMBIT_DIR:" $(GAMBIT_DIR)
	@echo "REFERENCES_DIR:" $(REFERENCES_DIR)
	@echo "DEACON_DIR:" $(DEACON_DIR)
	@echo "BIND_ROOTS:" $(BIND_ROOTS)

install: download_or_build_containers \
	databases \
	references \
	schemas

download_or_build_containers:
	$(call log_message,Checking if any containers need to be downloaded ...)
	@$(MAKE) -C $(CONTAINERS_SRC_DIR) CONTAINERS_DIR=$(CONTAINERS_DIR) all

schemas: $(addsuffix _all,$(SCHEMAS))

databases: gambit_db deacon_index

# The Kraken2 database is too large to download here; point the pipeline at an
# existing one (e.g. the JASEN one) with --kraken_db.
gambit_db: $(addprefix $(GAMBIT_DIR)/,$(GAMBIT_FILES))

$(GAMBIT_DIR)/%:
	$(call log_message,Downloading GAMBIT database file $* ...)
	mkdir -p $(GAMBIT_DIR) \
	&& wget "$(GAMBIT_URL)/$*" -O $@.tmp --no-verbose |& tee -a $(INSTALL_LOG) \
	&& [[ -s $@.tmp ]] \
	&& mv $@.tmp $@

deacon_index: $(DEACON_DIR)/$(DEACON_INDEX)

$(DEACON_DIR)/$(DEACON_INDEX):
	$(call log_message,Downloading Deacon human pangenome index (3.3 GB) ...)
	mkdir -p $(DEACON_DIR) \
	&& wget "$(DEACON_URL)" -O $@.tmp --no-verbose |& tee -a $(INSTALL_LOG) \
	&& [[ -s $@.tmp ]] \
	&& mv $@.tmp $@

# Each schema's reference genome (the reference column of assets/schemas.tsv),
# downloaded from NCBI Datasets with jasentool as FASTA and GFF, then indexed,
# plus its GenBank file for finding prophages with PhiSpy.
references: $(foreach accn,$(REFERENCES),$(REFERENCES_DIR)/$(accn).fasta $(REFERENCES_DIR)/$(accn).fasta.fai $(REFERENCES_DIR)/$(accn).gbff)

$(REFERENCES_DIR)/%.fasta:
	$(call log_message,Downloading reference genome $* ...)
	mkdir -p $(REFERENCES_DIR) \
	&& $(SINGULARITY) exec $(BIND_ARGS) $(CONTAINERS_DIR)/jasentool.sif \
		jasentool download-ncbi -i $* -o $(REFERENCES_DIR) |& tee -a $(INSTALL_LOG) \
	&& [[ -s $@ && -s $(REFERENCES_DIR)/$*.gff ]]

$(REFERENCES_DIR)/%.fasta.fai: $(REFERENCES_DIR)/%.fasta
	$(call log_message,Indexing reference genome $* ...)
	cd $(REFERENCES_DIR) \
	&& $(SINGULARITY) exec $(BIND_ARGS) $(CONTAINERS_DIR)/samtools.sif \
		samtools faidx $*.fasta |& tee -a $(INSTALL_LOG)

$(REFERENCES_DIR)/%.gbff:
	$(call log_message,Downloading GenBank file for reference genome $* ...)
	mkdir -p $(REFERENCES_DIR) \
	&& wget "$(NCBI_DATASETS)/$*/download?include_annotation_type=GENOME_GBFF&filename=$*.zip" \
		-O $@.zip --no-verbose |& tee -a $(INSTALL_LOG) \
	&& unzip -p $@.zip "ncbi_dataset/data/$*/genomic.gbff" > $@.tmp \
	&& [[ -s $@.tmp ]] \
	&& mv $@.tmp $@ \
	&& rm -f $@.zip

check: check_databases check_references check_schemas

check_databases:
	@status=0; \
	for file in $(GAMBIT_FILES); do \
		if [[ -s $(GAMBIT_DIR)/$$file ]]; then \
			echo "[✓] gambit: $(GAMBIT_DIR)/$$file"; \
		else \
			echo "[!] gambit: missing $(GAMBIT_DIR)/$$file"; status=1; \
		fi; \
	done; \
	if [[ -s $(DEACON_DIR)/$(DEACON_INDEX) ]]; then \
		echo "[✓] deacon: $(DEACON_DIR)/$(DEACON_INDEX)"; \
	else \
		echo "[!] deacon: missing $(DEACON_DIR)/$(DEACON_INDEX)"; status=1; \
	fi; \
	exit $$status

check_references:
	@status=0; \
	for accn in $(REFERENCES); do \
		for ext in fasta fasta.fai gff gbff; do \
			if [[ -s $(REFERENCES_DIR)/$$accn.$$ext ]]; then \
				echo "[✓] reference: $(REFERENCES_DIR)/$$accn.$$ext"; \
			else \
				echo "[!] reference: missing $(REFERENCES_DIR)/$$accn.$$ext"; status=1; \
			fi; \
		done; \
	done; \
	exit $$status

check_schemas:
	@status=0; \
	for schema in $(SCHEMAS); do \
		dir=$(SCHEMAS_DIR)/$$schema/alleles_rereffed; \
		if [[ -d $$dir ]]; then \
			echo "[✓] $$schema: $$dir ($$(find $$dir -maxdepth 1 -name '*.fasta' | wc -l | tr -d ' ') loci)"; \
		else \
			echo "[!] $$schema: missing $$dir"; status=1; \
		fi; \
	done; \
	exit $$status

# ==============================================================================
# Per-schema rules
# ==============================================================================
# $(1) is the schema name. Targets created for each schema:
#   <schema>_download_reference, <schema>_prodigal_training,
#   <schema>_download_schema, <schema>_unpack_schema, <schema>_prep_schema,
#   <schema>_all
define schema_rules
.PHONY: $(1)_all $(1)_download_reference $(1)_prodigal_training \
	$(1)_download_schema $(1)_unpack_schema $(1)_prep_schema

$(1)_all: $(1)_prep_schema

$(1)_download_reference: $(GENOMES_DIR)/$(SEED_$(1)).fasta

$(GENOMES_DIR)/$(SEED_$(1)).fasta:
	$$(call log_message,Downloading $(NAME_$(1)) seed genome $(SEED_$(1)) ...)
	mkdir -p $$(dir $$@) \
	&& wget "$(NCBI_EFETCH)&id=$(SEED_$(1))" -O $$@.tmp --no-verbose |& tee -a $(INSTALL_LOG) \
	&& grep -q '^>' $$@.tmp \
	&& mv $$@.tmp $$@

$(1)_prodigal_training: $(PRODIGAL_TRAINING_DIR)/$(1).trn

$(PRODIGAL_TRAINING_DIR)/$(1).trn: $(GENOMES_DIR)/$(SEED_$(1)).fasta
	$$(call log_message,Training Prodigal on $(NAME_$(1)) seed genome ...)
	mkdir -p $$(dir $$@) \
	&& $(SINGULARITY) exec $(BIND_ARGS) $(CONTAINERS_DIR)/prodigal.sif \
		prodigal -i $$< -t $$@ -p single |& tee -a $(INSTALL_LOG) \
	&& [[ -s $$@ ]]

$(1)_download_schema: $(SCHEMAS_DIR)/$(1)/download/$(ARCHIVE_$(1))

$(SCHEMAS_DIR)/$(1)/download/$(ARCHIVE_$(1)):
	$$(call log_message,Downloading $(NAME_$(1)) schema ...)
	mkdir -p $$(dir $$@) \
	&& if wget "$(URL_$(1))" -O $$@.tmp --no-verbose 2>> $(INSTALL_LOG) \
		&& $(if $(filter %.zip,$(ARCHIVE_$(1))),unzip -tq $$@.tmp > /dev/null,gzip -t $$@.tmp); then \
		mv $$@.tmp $$@ \
		&& echo "$(URL_$(1)) downloaded $$$$(date "+%Y-%m-%d")" > $$(dir $$@)/SOURCE; \
	else \
		rm -f $$@.tmp; \
		echo "[!] Could not download $(URL_$(1))"; \
		echo "    Download it in a browser and save it as $$@, then re-run make."; \
		exit 1; \
	fi

$(1)_unpack_schema: $(SCHEMAS_DIR)/$(1)/alleles/unpacking.done

$(SCHEMAS_DIR)/$(1)/alleles/unpacking.done: $(SCHEMAS_DIR)/$(1)/download/$(ARCHIVE_$(1))
	$$(call log_message,Unpacking $(NAME_$(1)) schema ...)
	mkdir -p $$(dir $$@) \
	&& if [[ $$< == *.zip ]]; then \
		unzip -DDqo $$< -d $$(dir $$@); \
	else \
		$(PYTHON) -I $(SCRIPT_DIR)/bin/split_alleles.py $$< $$(dir $$@) \
			$(if $(EXPECT_LOCI_$(1)),--expect-loci $(EXPECT_LOCI_$(1))); \
	fi |& tee -a $(INSTALL_LOG) \
	&& [[ $$$${PIPESTATUS[0]} -eq 0 ]] \
	&& echo $$$$(date "+%Y%m%d %H:%M:%S")": Done unpacking: " $$< > $$@

$(1)_prep_schema: $(SCHEMAS_DIR)/$(1)/alleles_rereffed

$(SCHEMAS_DIR)/$(1)/alleles_rereffed: $(PRODIGAL_TRAINING_DIR)/$(1).trn | $(SCHEMAS_DIR)/$(1)/alleles/unpacking.done
	$$(call log_message,Prepping $(NAME_$(1)) schema with chewBBACA ...)
	rm -rf $$@ $$@.tmp \
	&& $(SINGULARITY) exec $(BIND_ARGS) $(CONTAINERS_DIR)/chewbbaca.sif \
		chewie PrepExternalSchema \
		-g $(SCHEMAS_DIR)/$(1)/alleles \
		-o $$@.tmp \
		--cpu $(PREP_CPUS) \
		--ptf $$< |& tee -a $(INSTALL_LOG) \
	&& [[ $$$${PIPESTATUS[0]} -eq 0 ]] \
	&& mv $$@.tmp $$@ \
	&& find $(SCHEMAS_DIR)/$(1)/alleles -type f ! -name 'unpacking.done' -delete
endef

$(foreach schema,$(SCHEMAS),$(eval $(call schema_rules,$(schema))))
