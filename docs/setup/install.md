# Installation

## Requirements

- [Nextflow](https://www.nextflow.io) 25.04 or later
- Apptainer/Singularity, or Docker
- For the asset setup: GNU Make, `wget`, `unzip`, `gzip` and Python 3

## Get the pipeline

Nextflow can fetch it directly:

```bash
nextflow pull ryanjameskennedy/sinklink -r v0.1.0
```

The asset Makefiles need a local copy:

```bash
git clone git@github.com:ryanjameskennedy/sinklink.git
cd sinklink
make print_paths
```

## Set up the assets

The pipeline pulls its own containers (the versions pinned by each nf-core
module, see [software](../reference/software.md)). The Makefiles only set up
what the pipeline reads: the chewBBACA schemas, the reference genomes, the
Deacon human index, the GAMBIT database and the four containers needed to
prepare them (chewBBACA, Prodigal, jasentool and SAMtools).

```bash
make install ASSETS_DIR=/mnt/cache/dbs/vask CONTAINERS_DIR=/mnt/cache/singularity
```

or step by step:

```bash
make -C containers all CONTAINERS_DIR=/mnt/cache/singularity
make databases ASSETS_DIR=/mnt/cache/dbs/vask
make references ASSETS_DIR=/mnt/cache/dbs/vask CONTAINERS_DIR=/mnt/cache/singularity
make schemas ASSETS_DIR=/mnt/cache/dbs/vask CONTAINERS_DIR=/mnt/cache/singularity
make check ASSETS_DIR=/mnt/cache/dbs/vask
```

- [Schemas](schemas.md): what `make schemas` does and what to do when a
  download fails.
- [Databases](databases.md): reference genomes, Deacon, GAMBIT, and how to
  download the Kraken2/Bracken database, which `make install` leaves out.

Then [run the pipeline](../usage.md).
