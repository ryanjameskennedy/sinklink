# sinklink: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.0.0dev - [unreleased]

Initial release of sinklink, created with the [nf-core](https://nf-co.re/) template.

### `Added`

- Read preparation: optional Trimmomatic (Illumina) and Filtlong (Nanopore), FastQC and NanoPlot
- Assembly: SKESA or SPAdes for Illumina, Flye and Medaka for Nanopore
- Assembly QC: QUAST, gambitcore, read depth over the own assembly, 7-gene MLST
- Species check with Kraken2 and Bracken against the species each schema covers
- chewBBACA AlleleCall per schema and pairwise distances within transmission groups, flagged by QC
- Makefile for schema setup (seed genome, Prodigal training, download, PrepExternalSchema) and the GAMBIT database
- `thedonkey` profile and a stub `test` profile

### `Fixed`

### `Dependencies`

### `Deprecated`
