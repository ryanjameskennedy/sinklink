# Installation

## Requirements

- [Nextflow](https://www.nextflow.io) 25.04 or later
- Apptainer/Singularity, or Docker
- For the asset setup: GNU Make, `wget`, `unzip`, `gzip` and Python 3

## Get the pipeline

Nextflow can fetch it directly:

```bash
nextflow pull ryanjameskennedy/sinklink -r master
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
what the pipeline reads: the chewBBACA schemas, the GAMBIT database and the
two containers needed to prepare the schemas.

```bash
make install ASSETS_DIR=/mnt/cache/dbs/vask CONTAINERS_DIR=/mnt/cache/singularity
```

or step by step:

```bash
make -C containers all CONTAINERS_DIR=/mnt/cache/singularity
make databases ASSETS_DIR=/mnt/cache/dbs/vask
make schemas ASSETS_DIR=/mnt/cache/dbs/vask CONTAINERS_DIR=/mnt/cache/singularity
make check ASSETS_DIR=/mnt/cache/dbs/vask
```

- [Schemas](schemas.md): what `make schemas` does and what to do when a
  download fails.
- [Databases](databases.md): GAMBIT and Kraken2/Bracken.

Then [run the pipeline](../usage.md).
