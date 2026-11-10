# sinklink: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

### `Added`

- SNP distances from masked pseudogenomes built with existing tools: repeats from a MUMmer self-alignment and prophages from PhiSpy are masked with the low-depth regions (mosdepth) when `bcftools consensus` applies each isolate's SNPs; Gubbins removes recombination for schemas with 3 or more sequences and snp-dists counts the differences
- `make references` also downloads each reference's GenBank file for PhiSpy
- `snp_recombination_filtered` in the pair table
- Links from the species threshold table to each threshold's source, and DOIs for the Kampmeier, Kieninger and Prior papers

### `Changed`

- The setup Makefiles run their containers with `singularity` (`SINGULARITY=apptainer` switches runtime)
- The setup examples keep the databases directly under `/mnt/cache/dbs`
- The run examples use `-profile singularity`, as thedonkey's config now sets up Singularity

### `Fixed`

- A `0` allele call counts as missing, as in cgmlst-dists, so two missing calls never count as a match
- PhiSpy finds its GenBank output when the input file name has dots, such as an NCBI accession (nf-core module patch)
- `make references` keeps the reference FASTA files; make treated them as temporary and deleted them after indexing
- Setup log messages with brackets no longer break the shell command
- The species check tables on the _K. oxytoca_, _K. pneumoniae_ and _S. marcescens_ pages, which the `|` in their species patterns split into extra columns

### `Removed`

- The home-made pseudogenome script (`make_pseudogenome.py`) and the samtools depth step, replaced by the tools above
- `snp_sites_compared` in the pair table

## v0.2.0 - 2026-11-08

Adds human read removal, variant calling against a reference genome per species
and SNP distances next to the allele distances, and moves server settings out of
the pipeline. Tested with stub runs only; not yet validated on real data.

### `Added`

- Documentation on running on a server, with each tool's label and its nf-core, JASEN and thedonkey resources
- nf-core template features: nf-test tests with snapshots, the template CI (linting, nf-test, branch protection), RO-Crate metadata, nf-core/configs profiles, and email, Slack and Teams notifications
- `lims_id` metadata column, shown in the allele QC and pair tables
- Metro map of the pipeline (`assets/metro_map.mmd`, drawn with nf-metro) in the README and docs
- Human read removal with Deacon and the `panhuman-1` index before every other step (`--deacon_index`, `--skip_host_removal`, `--save_host_removed_reads`; `make deacon_index`)
- A reference genome per schema (NCBI RefSeq reference, `reference` column of `assets/schemas.tsv`), downloaded with jasentool as FASTA and GFF by `make references` (`--references_dir`)
- QUAST compares each assembly with its reference genome, and the QC summary reports the genome fraction and the Mash distance to the reference, with a `distant_reference` warning above 0.05
- Variant calling against the reference genome: Snippy for Illumina, minimap2 and Clair3 (bacterial model, `--clair3_model`) for Nanopore, published as VCFs (`--skip_variant_calling`)
- A masked pseudogenome per isolate and pairwise SNP distances within each transmission group, reported next to the allele differences (`--snp_min_depth`)
- `test_full` profile (the test inputs with every optional step on), which `nf-core pipelines download` needs to list the containers
- A test with host removal, variant calling and allele calling skipped
- Docs on how to download the Standard-16 Kraken2 database, and on what the species thresholds mean for calling the same colonisation
- `containers/Makefile` also downloads jasentool and samtools for `make references`

### `Changed`

- SKESA and chewBBACA use their nf-core label resources instead of custom ones
- Labels follow the JASEN resources: SKESA, chewBBACA and Snippy `process_high`, NanoPlot, gambitcore and minimap2 `process_medium` (nf-core module patches)
- Removed the `thedonkey` profile: pass the server config with `-c` and the database paths with `-params-file` (see ryanjameskennedy/configs)
- Metadata columns: `translation_id` is now `sample` and `sample` (the sample type) is now `sample_type`; the QC tables use `sample` too
- The stub CI workflow `ci.yml` is replaced by nf-test
- The test samplesheet points at the test reads on GitHub, so tests run from any folder
- `--kraken_db` is required and the Kraken2/Bracken species check always runs
- The distance check also runs with `--skip_chewbbaca`, reporting SNP distances only
- Metadata dates are read as ISO 8601 date-times (`YYYY-MM-DDTHH:MM:SS`, or `YYYY-MM-DD`)
- The setup's chewBBACA and samtools images are the ones the pipeline uses, saved under the names Nextflow caches them as, so the pipeline reuses them when `CONTAINERS_DIR` is its Apptainer cache
- The nf-test and pipeline download CI jobs run on Ubuntu 24.04, and the download job tests the pull request's own branch
- Pull requests into `master` may also come from `release/*` branches

### `Fixed`

- The chewBBACA version is read from its version line only; the Python warning chewBBACA 3.5.4 prints made the software versions file invalid
- Clair3 finds its bundled models under Apptainer (nf-core module patch)
- The local modules use their Singularity images under Apptainer, as the nf-core modules do

### `Removed`

- SPAdes and the `--assembler` parameter: Illumina reads are always assembled with SKESA
- The nf-core template version comment workflow, which needs the nf-core bot's token

## v0.1.0 - 2026-11-06

First release of sinklink, created with the [nf-core](https://nf-co.re/) template.
Tested with stub runs only; not yet validated on real data.

### `Added`

- Read preparation: optional Trimmomatic (Illumina) and Filtlong (Nanopore), FastQC and NanoPlot
- Assembly: SKESA or SPAdes for Illumina, Flye and Medaka for Nanopore
- Assembly QC: QUAST, gambitcore, read depth over the own assembly, 7-gene MLST
- Species check with Kraken2 and Bracken against the species each schema covers
- chewBBACA AlleleCall per schema and pairwise distances within transmission groups, flagged by QC
- Makefile for schema setup (seed genome, Prodigal training, download, PrepExternalSchema) and the GAMBIT database
- `thedonkey` profile and a stub `test` profile
- Documentation on Read the Docs, with one page per species and the source of each threshold
- GitHub Actions: stub runs on Nextflow 25.04.0 and a strict docs build

### `Fixed`

### `Dependencies`

### `Deprecated`
