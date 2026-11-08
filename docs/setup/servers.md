# Running on a server

sinklink keeps no server settings of its own. Following nf-core, a server is
described by two files that you pass at run time:

- a **config** (`-c`) for resources and infrastructure: the work directory, the
  executor caps, CPU and memory per tool, and the container cache;
- a **parameters file** (`-params-file`) for the database paths.

nf-core asks for parameters to stay out of `-c` configs, so the two are kept
apart.

The configs for our own servers live in
[ryanjameskennedy/configs](https://github.com/ryanjameskennedy/configs), next to
the JASEN ones. On thedonkey:

```bash
tmux new -s sinklink 'nextflow run ryanjameskennedy/sinklink -r v0.1.0 -profile apptainer \
    -c /path/to/configs/sinklink/thedonkey.config \
    -params-file /path/to/configs/sinklink/thedonkey.yaml \
    --input samplesheet.csv --metadata vask_colonisation_hidden.csv \
    --outdir /media/Lagring/$USER/vask'
```

`tmux` keeps the run going if the connection drops. Add `-resume` to continue a
stopped run.

## What goes where

| Setting                                          | File            | thedonkey                                                     |
| ------------------------------------------------ | --------------- | ------------------------------------------------------------- |
| `--schemas_dir`                                  | parameters file | `/mnt/cache/dbs/vask/schemas`                                 |
| `--kraken_db`                                    | parameters file | `/mnt/cache/dbs/kraken2/standard_16gb_20260626` (Standard-16) |
| `--deacon_index`                                 | parameters file | `/mnt/cache/dbs/vask/deacon/panhuman-1.k31w15.idx`            |
| `--references_dir`                               | parameters file | `/mnt/cache/dbs/vask/references`                              |
| `--gambit_db`                                    | parameters file | `/mnt/cache/dbs/gambit_db`                                    |
| Work directory                                   | config          | `/media/shortterm/$USER/work`                                 |
| Total CPUs and memory in use (`executor.$local`) | config          | 15 CPUs, 141 GB, at most 8 tasks                              |
| Largest single task (`process.resourceLimits`)   | config          | 15 CPUs, 141 GB, 48 h                                         |
| CPUs and memory per tool                         | config          | see [resources](#resources)                                   |
| Apptainer cache and bind mounts                  | config          | `/mnt/cache/singularity`, `--bind /mnt/cache/dbs`             |

thedonkey has 20 threads and 188 GB and is shared with two colleagues without a
scheduler, so the caps sit about 25% below the machine totals.

`--kraken_db`, `--deacon_index`, `--references_dir` and `--schemas_dir` are
required unless the matching `--skip_*` option is set. Without `--gambit_db`
gambitcore is skipped.

To see what a config resolves to before a run:

```bash
nextflow -c /path/to/configs/sinklink/thedonkey.config config ryanjameskennedy/sinklink \
    -profile apptainer -flat | grep -E "resourceLimits|withLabel|withName.*(cpus|memory)"
```

## Resources

Every process carries a size label: `process_single`, `process_low`,
`process_medium` or `process_high`. The pipeline's `conf/base.config` sets what
each label gets, using the nf-core template values, and a server config can
resize a whole label with `withLabel` or one tool with `withName`.

nf-core modules come with a label chosen by the module's authors. sinklink
changes it for six tools, so that each label matches the resources JASEN gives
the tool on the same server. For the five nf-core modules the change is recorded
as a module patch (`modules/nf-core/<tool>/<tool>.diff`, listed in
`modules.json`), which nf-core lint accepts and `nf-core modules update` keeps.

| Tool                      | nf-core label    | sinklink label   | Why                   |
| ------------------------- | ---------------- | ---------------- | --------------------- |
| SKESA                     | `process_single` | `process_high`   | JASEN: 16 CPUs, 32 GB |
| chewBBACA AlleleCall      | `process_low`    | `process_high`   | JASEN: 16 CPUs, 12 GB |
| NanoPlot                  | `process_low`    | `process_medium` | JASEN: 4 CPUs         |
| gambitcore (local module) | `process_low`    | `process_medium` | JASEN: 4 CPUs, 8 GB   |
| minimap2                  | `process_high`   | `process_medium` | JASEN: 4 CPUs, 12 GB  |
| Snippy                    | `process_low`    | `process_high`   | JASEN: 16 CPUs, 32 GB |

The Clair3 module also carries a patch that lets it find its bundled models
under Apptainer, which the module otherwise only allows for Singularity,
Docker and Podman.

samtools index stays at `process_low` although JASEN gives it 16 CPUs: it
indexes one BAM in seconds, and `process_high` would hold every CPU on
thedonkey while it does.

thedonkey's config then resizes the labels themselves towards the JASEN values:

| Label            | Pipeline default     | thedonkey            |
| ---------------- | -------------------- | -------------------- |
| `process_single` | 1 CPU, 6 GB, 4 h     | 1 CPU, 2 GB, 4 h     |
| `process_low`    | 2 CPUs, 12 GB, 4 h   | 2 CPUs, 4 GB, 4 h    |
| `process_medium` | 6 CPUs, 36 GB, 8 h   | 4 CPUs, 12 GB, 8 h   |
| `process_high`   | 12 CPUs, 72 GB, 16 h | 15 CPUs, 32 GB, 16 h |

| Tool                                                 | Label            | Pipeline default         | JASEN           | thedonkey                |
| ---------------------------------------------------- | ---------------- | ------------------------ | --------------- | ------------------------ |
| Deacon                                               | `process_medium` | 6 CPUs, 36 GB            | –               | 4 CPUs, 12 GB            |
| FastQC                                               | `process_medium` | 6 CPUs, 36 GB            | 4 CPUs, 2 GB    | 4 CPUs, 12 GB            |
| NanoPlot                                             | `process_medium` | 6 CPUs, 36 GB            | 4 CPUs, 2 GB    | 4 CPUs, 12 GB            |
| Trimmomatic                                          | `process_medium` | 6 CPUs, 36 GB            | 4 CPUs, 4 GB    | 4 CPUs, 12 GB            |
| Filtlong                                             | `process_low`    | 2 CPUs, 12 GB            | 2 CPUs, 4 GB    | 2 CPUs, 4 GB             |
| SKESA                                                | `process_high`   | 12 CPUs, 72 GB           | 16 CPUs, 32 GB  | 15 CPUs, 32 GB           |
| Flye                                                 | `process_high`   | 12 CPUs, 72 GB           | 20 CPUs, 32 GB  | 15 CPUs, 32 GB           |
| Medaka                                               | `process_high`   | 12 CPUs, 72 GB           | 20 CPUs, 32 GB  | 15 CPUs, 32 GB           |
| QUAST                                                | `process_medium` | 6 CPUs, 36 GB            | 2 CPUs, 2 GB    | 4 CPUs, 12 GB            |
| gambitcore                                           | `process_medium` | 6 CPUs, 36 GB            | 4 CPUs, 8 GB    | 4 CPUs, 12 GB            |
| bwa index                                            | none             | 1 CPU, 7 × assembly size | 2 CPUs, 2 GB    | 1 CPU, 7 × assembly size |
| bwa mem                                              | `process_high`   | 12 CPUs, 72 GB           | 16 CPUs, 20 GB  | 15 CPUs, 32 GB           |
| minimap2                                             | `process_medium` | 6 CPUs, 36 GB            | 4 CPUs, 12 GB   | 4 CPUs, 12 GB            |
| samtools index                                       | `process_low`    | 2 CPUs, 12 GB            | 16 CPUs, 2 GB   | 2 CPUs, 4 GB             |
| samtools coverage                                    | `process_single` | 1 CPU, 6 GB              | 2 CPUs, 2 GB    | 1 CPU, 2 GB              |
| mlst                                                 | `process_low`    | 2 CPUs, 12 GB            | 2 CPUs, 2 GB    | 2 CPUs, 4 GB             |
| Mash                                                 | `process_low`    | 2 CPUs, 12 GB            | –               | 2 CPUs, 4 GB             |
| Snippy                                               | `process_high`   | 12 CPUs, 72 GB           | 16 CPUs, 32 GB  | 15 CPUs, 32 GB           |
| minimap2 to the reference                            | `process_medium` | 6 CPUs, 36 GB            | 4 CPUs, 12 GB   | 4 CPUs, 12 GB            |
| Clair3                                               | `process_high`   | 12 CPUs, 72 GB           | 8 CPUs, 16 GB   | 15 CPUs, 32 GB           |
| samtools depth                                       | `process_low`    | 2 CPUs, 12 GB            | –               | 2 CPUs, 4 GB             |
| Kraken2                                              | `process_high`   | 12 CPUs, 72 GB           | 16 CPUs, 100 GB | 15 CPUs, 32 GB           |
| Bracken                                              | `process_low`    | 2 CPUs, 12 GB            | 2 CPUs, 2 GB    | 2 CPUs, 4 GB             |
| chewBBACA AlleleCall                                 | `process_high`   | 12 CPUs, 72 GB           | 16 CPUs, 12 GB  | 15 CPUs, 32 GB           |
| gunzip, pseudogenome, QC summary, distances, MultiQC | `process_single` | 1 CPU, 6 GB              | –               | 1 CPU, 2 GB              |

Every tool follows its label on thedonkey; none is set on its own. JASEN gives
Kraken2 100 GB for the full standard database, but sinklink uses Standard-16,
which needs at most 16 GB and is read with `--memory-mapping`. Where JASEN asks
for more than 15 CPUs, thedonkey's cap applies.

How the settings combine:

- `withName` always wins over `withLabel`, whichever file it is in, and a `-c`
  config wins over the pipeline's own settings of the same kind.
- A label can only be resized, not added: Nextflow ignores a `label` set from a
  config. To group tools, list them in one selector, e.g.
  `withName: 'SKESA|CHEWBBACA_ALLELECALL'`.
- A task that runs out of memory or time is retried once with double the
  memory and time, still capped by `resourceLimits`.
- The local executor runs as many tasks as fit under its total caps; the rest
  wait.

The JASEN-derived values have not yet been checked against real sinklink runs.
Each run writes `pipeline_info/execution_trace_*.txt` with every task's peak
memory and run time; use it to adjust the config.

## Other servers

Copy the two thedonkey files and change the paths and caps. On a machine of
your own, `process.resourceLimits` set to the machine's size is often all the
config needs, and the nf-core label sizes apply unchanged. See the nf-core
pages on
[max resources](https://nf-co.re/docs/usage/configuration#max-resources) and
[tuning workflow resources](https://nf-co.re/docs/usage/configuration#tuning-workflow-resources).
