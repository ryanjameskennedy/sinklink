# thedonkey profile

`-profile thedonkey` loads
[`conf/thedonkey.config`](https://github.com/ryanjameskennedy/sinklink/blob/master/conf/thedonkey.config)
on top of the defaults.

```bash
nextflow run ryanjameskennedy/sinklink -r v0.1.0 -profile thedonkey \
    --input samplesheet.csv \
    --metadata vask_colonisation_hidden.csv \
    --outdir /media/Lagring/$USER/vask
```

## What it sets

**Database paths**

| Parameter | Value |
|---|---|
| `--schemas_dir` | `/mnt/cache/dbs/vask/schemas` (from `make schemas ASSETS_DIR=/mnt/cache/dbs/vask`) |
| `--kraken_db` | `/mnt/cache/dbs/kraken2/standard_2025-06` (the JASEN database) |
| `--gambit_db` | `/mnt/cache/dbs/gambit_db` |

Any of them can be overridden on the command line.

**Resource caps.** thedonkey has 20 threads and 188 GB, shared with two
colleagues, and no scheduler. The profile uses the local executor capped at 15
CPUs and 141 GB in total, and no single task may ask for more than 15 CPUs,
141 GB or 48 h. Within those caps Nextflow runs as many tasks as fit: one Flye
job (`process_high`: 12 CPUs, 72 GB) can run alongside a few MLST or
Bracken jobs (`process_low`: 2 CPUs, 12 GB).

**Kraken2 one job at a time.** It reads the large standard database
memory-mapped, so one job keeps memory predictable.

**Apptainer.** Images are cached in `/mnt/cache/singularity` and
`/mnt/cache/dbs` is bound into the containers. Each tool's image is downloaded
once on the first run.

**Work directory.** Intermediate files go to `/media/shortterm/$USER/work`;
`-resume` picks up from there.
