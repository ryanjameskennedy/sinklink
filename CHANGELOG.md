# sinklink: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

### `Added`

- Documentation on running on a server, with each tool's label and its nf-core, JASEN and thedonkey resources
- nf-core template features: nf-test tests with snapshots, the template CI (linting, nf-test, branch protection), RO-Crate metadata, nf-core/configs profiles, and email, Slack and Teams notifications
- `lims_id` metadata column, shown in the allele QC and pair tables

### `Changed`

- SKESA and chewBBACA use their nf-core label resources instead of custom ones
- Labels follow the JASEN resources: SKESA and chewBBACA `process_high`, NanoPlot, gambitcore and minimap2 `process_medium` (nf-core module patches)
- Removed the `thedonkey` profile: pass the server config with `-c` and the database paths with `-params-file` (see ryanjameskennedy/configs)
- Metadata columns: `translation_id` is now `sample` and `sample` (the sample type) is now `sample_type`; the QC tables use `sample` too
- The stub CI workflow `ci.yml` is replaced by nf-test
- The test samplesheet points at the test reads on GitHub, so tests run from any folder

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
