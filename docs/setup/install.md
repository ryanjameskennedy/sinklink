# Installation

## Requirements

- [Nextflow](https://www.nextflow.io) 25.04 or later
- Apptainer/Singularity, or Docker
- For the asset setup: GNU Make, `wget`, `unzip`, `gzip` and Python 3

## Get the pipeline

Nextflow can fetch it directly:

```bash
nextflow pull ryanjameskennedy/sinklink -r v0.4.0
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

The containers are built with `singularity` and saved under the names Nextflow
uses in its Singularity/Apptainer cache,
and the chewBBACA and SAMtools images are the ones the pipeline runs. Use the
same folder for `CONTAINERS_DIR` as `singularity.cacheDir` in your server config
(on thedonkey, `/mnt/cache/singularity`) and the pipeline reuses those two
instead of downloading them again; it pulls the rest itself on its first run.

```bash
make install ASSETS_DIR=/mnt/cache/dbs CONTAINERS_DIR=/mnt/cache/singularity
```

or step by step:

```bash
make -C containers all CONTAINERS_DIR=/mnt/cache/singularity
make databases ASSETS_DIR=/mnt/cache/dbs
make references ASSETS_DIR=/mnt/cache/dbs CONTAINERS_DIR=/mnt/cache/singularity
make schemas ASSETS_DIR=/mnt/cache/dbs CONTAINERS_DIR=/mnt/cache/singularity
make check ASSETS_DIR=/mnt/cache/dbs
```

- [Schemas](schemas.md): what `make schemas` does and what to do when a
  download fails.
- [Databases](databases.md): reference genomes, Deacon, GAMBIT, and how to
  download the Kraken2/Bracken database with `make kraken_db`, which
  `make install` leaves out.

Then [run the pipeline](../usage.md).
