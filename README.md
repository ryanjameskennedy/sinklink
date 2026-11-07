# sinklink

[![nf-test](https://github.com/ryanjameskennedy/sinklink/actions/workflows/nf-test.yml/badge.svg)](https://github.com/ryanjameskennedy/sinklink/actions/workflows/nf-test.yml)
[![Docs](https://readthedocs.org/projects/sinklink/badge/?version=latest)](https://sinklink.readthedocs.io)
[![Nextflow](https://img.shields.io/badge/nextflow-%E2%89%A525.04.0-23aa62.svg)](https://www.nextflow.io/)

*Did the sink infect the patient?*

sinklink tests whether bacteria isolated from a hospital sink (or another
environmental site) and from a patient belong to the same strain. Starting from
Illumina or Nanopore reads, it:

1. QCs the reads (FastQC or NanoPlot, optional Trimmomatic or Filtlong);
2. assembles each isolate (SKESA or SPAdes for Illumina, Flye + Medaka for Nanopore);
3. QCs the assembly (QUAST, gambitcore, read depth, 7-gene MLST) and confirms
   the species from the reads (Kraken2/Bracken);
4. calls alleles with chewBBACA against species-specific cgMLST/wgMLST schemas;
5. compares every pair of isolates within each suspected transmission group
   against a published, species-specific allele-difference threshold, flagging
   pairs where either isolate failed QC.

It is a Nextflow pipeline built on the [nf-core](https://nf-co.re) template,
modelled on [JASEN](https://github.com/genomic-medicine-sweden/JASEN), and runs
on a single server without a job scheduler.

**Documentation: <https://sinklink.readthedocs.io>**

## Quick start

Set up the schemas and databases once:

```bash
git clone git@github.com:ryanjameskennedy/sinklink.git && cd sinklink
make install ASSETS_DIR=/mnt/cache/dbs/vask CONTAINERS_DIR=/mnt/cache/singularity
```

Then run every isolate, whatever its species, with one samplesheet and one
metadata file:

```bash
nextflow run ryanjameskennedy/sinklink -r v0.1.0 -profile apptainer \
    -c thedonkey.config -params-file thedonkey.yaml \
    --input samplesheet.csv \
    --metadata metadata.csv \
    --outdir results
```

```text
sample,platform,fastq_1,fastq_2
S01,illumina,/data/reads/S01_R1.fastq.gz,/data/reads/S01_R2.fastq.gz
S02,nanopore,/data/reads/S02.fastq.gz,
```

The metadata needs `sample`, `transmission` and `growth` columns. See
[running sinklink](https://sinklink.readthedocs.io/en/latest/usage.html) for
the formats and [running on a server](https://sinklink.readthedocs.io/en/latest/setup/servers.html)
for the `-c` config and parameters file.

## Species and thresholds

| Species | Threshold (alleles) | Threshold from |
|---|---|---|
| *Pseudomonas aeruginosa* | ≤12 | cgmlst.org complex type distance |
| *Klebsiella pneumoniae* species complex | ≤15 | cgmlst.org complex type distance |
| *Klebsiella oxytoca* species complex | ≤6 (borderline ≤9) | Dabernig-Heinz et al. 2024 |
| *Serratia marcescens* | ≤12 | cgmlst.org complex type distance |
| *Citrobacter freundii* | ≤10 | cgmlst.org complex type distance |
| *Enterobacter hormaechei* | ≤12 | cgmlst.org complex type distance |
| *Stenotrophomonas maltophilia* complex | ≤10 | Gröschel et al. 2020 (d10) |

Each species has its own page, with the scheme, the paper behind it and the
species the scheme accepts:
[species and thresholds](https://sinklink.readthedocs.io/en/latest/species/index.html).

## Data

The VASK study metadata (`vask_colonisation_hidden.csv`) contains study patient
identifiers and is not part of this repository; it is git-ignored.

## Citations

Tools used by the pipeline are listed in [CITATIONS.md](CITATIONS.md), and the
literature behind the thresholds in the
[references](https://sinklink.readthedocs.io/en/latest/reference/references.html).
