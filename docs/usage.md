# Running sinklink

## One run for all species

One samplesheet and one metadata file cover every isolate, whatever its
species. sinklink reads each isolate's `growth` label from the metadata, picks
its schema, and groups the assemblies by schema for allele calling (one
chewBBACA job per schema). Pairs are only compared within a transmission group,
and only when both isolates were typed with the same schema. There is no need
for one CSV per species.

## Samplesheet input

The samplesheet (`--input`) lists the reads for each isolate: a CSV with a
header row and 4 columns.

```text
sample,platform,fastq_1,fastq_2
S01,illumina,/data/reads/S01_R1.fastq.gz,/data/reads/S01_R2.fastq.gz
S02,illumina,/data/reads/S02.fastq.gz,
S03,nanopore,/data/reads/S03.fastq.gz,
```

| Column     | Description                                                                                              |
| ---------- | -------------------------------------------------------------------------------------------------------- |
| `sample`   | Isolate ID, matching `sample` in the metadata. Letters, digits, `.`, `_` and `-` only; each sample once. |
| `platform` | `illumina` or `nanopore`.                                                                                |
| `fastq_1`  | Gzipped FastQ (`.fastq.gz` or `.fq.gz`): read 1, single-end reads or Nanopore reads.                     |
| `fastq_2`  | Gzipped FastQ for Illumina read 2. Leave empty for single-end and Nanopore reads.                        |

The samplesheet is checked against
[`assets/schema_input.json`](https://github.com/ryanjameskennedy/sinklink/blob/master/assets/schema_input.json)
before anything runs: the files must exist, and a Nanopore row with a
`fastq_2` is rejected. Use absolute paths; relative paths are resolved from the
folder you launch from. Several runs of one isolate are not merged, so
concatenate them first. An
[example samplesheet](https://github.com/ryanjameskennedy/sinklink/blob/master/assets/samplesheet.csv)
is provided.

## Metadata input

The metadata (`--metadata`) describes the study: a CSV with one row per
isolate.

```text
transmission,sample,lims_id,studypatientnumber,sample_type,date,growth,comment
Transmission_1,S01,LIMS-0001,P1,environment,2024-01-01T09:30:00,pseudomonas_aeruginosa,
Transmission_1,S02,LIMS-0002,P1,airway,2024-01-20T14:06:00,pseudomonas_aeruginosa,
```

| Column               | Required | Description                                                                                                                            |
| -------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `transmission`       | yes      | Suspected transmission group; isolates in the same group are compared pairwise                                                         |
| `sample`             | yes      | Isolate ID, matching `sample` in the samplesheet                                                                                       |
| `lims_id`            | no       | Laboratory (LIMS) ID, shown in the allele QC and pair tables                                                                           |
| `studypatientnumber` | no       | Study patient, shown in the pair table                                                                                                 |
| `sample_type`        | no       | Sample type, e.g. `environment` or `airway`, shown in the pair table                                                                   |
| `date`               | no       | Sampling date and time in ISO 8601 (`YYYY-MM-DDTHH:MM:SS`, e.g. `2024-01-20T14:06:00`; `YYYY-MM-DD` also works), used for `days_apart` |
| `growth`             | yes      | Species reported by the laboratory, mapped to a schema by `assets/species_map.tsv` (exact match)                                       |
| `comment`            | no       | Free text; not used by the pipeline                                                                                                    |

Column order does not matter, other columns are ignored and quoted commas are
fine.

How it is used:

1. **At start-up**, each samplesheet row is matched to its metadata row.
   `growth` gives the schema, and the schema's genome size range in
   `assets/schemas.tsv` gives the expected genome size passed to Flye (for
   _P. aeruginosa_, 5.5–7.8 Mb becomes `6.7m`) and the reference genome used
   for QUAST, Mash and variant calling. The run stops if a required column is
   missing.
2. An isolate missing from the metadata, or whose `growth` has no schema, gets a
   warning and is assembled and QC'd but not allele called or variant called.
   The same goes for a schema that is not set up in `--schemas_dir`, or whose
   reference genome is not in `--references_dir`.
3. **Allele calling** groups the assemblies by schema.
4. **Variant calling** maps each isolate's reads to its schema's reference
   genome.
5. **The QC summary** uses the schema's accepted species, genome size and
   reference genome.
6. **The distance check** pairs isolates within each transmission group. Every
   metadata row is included, so isolates listed in the metadata but missing
   from the samplesheet show up as `missing_profile`.

## Running the pipeline

```bash
nextflow run ryanjameskennedy/sinklink -r v0.1.0 \
    -profile apptainer \
    --input samplesheet.csv \
    --metadata metadata.csv \
    --schemas_dir /path/to/schemas \
    --kraken_db /path/to/kraken2_db \
    --deacon_index /path/to/deacon/panhuman-1.k31w15.idx \
    --references_dir /path/to/references \
    --gambit_db /path/to/gambit_db \
    --outdir results
```

`--kraken_db` is always required. `--deacon_index`, `--references_dir` and
`--schemas_dir` are required unless `--skip_host_removal`,
`--skip_variant_calling` or `--skip_chewbbaca` turns off the step that needs
them. `make install` sets up everything except the Kraken2 database (see
[installation](setup/install.md)).

For Nanopore isolates, set `--clair3_model` to the Clair3 model that matches
the flow cell and basecaller if the default, fine-tuned on bacterial R10.4.1
SUP data, does not fit.

On a server, put the database paths in a parameters file and the resources in
a config (see [running on a server](setup/servers.md)):

```bash
nextflow run ryanjameskennedy/sinklink -r v0.1.0 -profile apptainer \
    -c thedonkey.config -params-file thedonkey.yaml \
    --input samplesheet.csv --metadata vask_colonisation_hidden.csv \
    --outdir /media/Lagring/$USER/vask
```

All options are listed under [parameters](reference/parameters.md). Nextflow
keeps intermediate files in the work directory; add `-resume` to continue a
stopped run.

A stub test with placeholder inputs checks the wiring without real data (run
from the repository root):

```bash
nextflow run . -profile test,docker -stub --outdir results
```

## Updating the pipeline

When you run the above command, Nextflow automatically pulls the pipeline code from GitHub and stores it as a cached version. When running the pipeline after this, it will always use the cached version if available - even if the pipeline has been updated since. To make sure that you're running the latest version of the pipeline, make sure that you regularly update the cached version of the pipeline:

```bash
nextflow pull ryanjameskennedy/sinklink
```

## Reproducibility

It is a good idea to specify the pipeline version when running the pipeline on your data. This ensures that a specific version of the pipeline code and software are used when you run your pipeline. If you keep using the same tag, you'll be running the same version of the pipeline, even if there have been changes to the code since.

First, go to the [sinklink releases page](https://github.com/ryanjameskennedy/sinklink/releases) and find the latest pipeline version - numeric only (eg. `1.3.1`). Then specify this when running the pipeline with `-r` (one hyphen) - eg. `-r 1.3.1`. Of course, you can switch to another version by changing the number after the `-r` flag.

This version number will be logged in reports when you run the pipeline, so that you'll know what you used when you look back in the future. For example, at the bottom of the MultiQC reports.

To further assist in reproducibility, you can use share and reuse [parameter files](#running-the-pipeline) to repeat pipeline runs with the same settings without having to write out a command with every single parameter.

> [!TIP]
> If you wish to share such profile (such as upload as supplementary material for academic publications), make sure to NOT include cluster specific paths to files, nor institutional specific profiles.

## Core Nextflow arguments

> [!NOTE]
> These options are part of Nextflow and use a _single_ hyphen (pipeline parameters use a double-hyphen)

### `-profile`

Use this parameter to choose a configuration profile. Profiles can give configuration presets for different compute environments.

Several generic profiles are bundled with the pipeline which instruct the pipeline to use software packaged using different methods (Docker, Singularity, Podman, Shifter, Charliecloud, Apptainer, Conda) - see below.

> [!IMPORTANT]
> We highly recommend the use of Docker or Singularity containers for full pipeline reproducibility, however when this is not possible, Conda is also supported.

The pipeline also dynamically loads configurations from [https://github.com/nf-core/configs](https://github.com/nf-core/configs) when it runs, making multiple config profiles for various institutional clusters available at run time. For more information and to check if your system is supported, please see the [nf-core/configs documentation](https://github.com/nf-core/configs#documentation).

Note that multiple profiles can be loaded, for example: `-profile test,docker` - the order of arguments is important!
They are loaded in sequence, so later profiles can overwrite earlier profiles.

If `-profile` is not specified, the pipeline will run locally and expect all software to be installed and available on the `PATH`. This is _not_ recommended, since it can lead to different results on different machines dependent on the computer environment.

- `test`
  - A profile with a complete configuration for automated testing
  - Includes links to test data so needs no other parameters
- `docker`
  - A generic configuration profile to be used with [Docker](https://docker.com/)
- `singularity`
  - A generic configuration profile to be used with [Singularity](https://sylabs.io/docs/)
- `podman`
  - A generic configuration profile to be used with [Podman](https://podman.io/)
- `shifter`
  - A generic configuration profile to be used with [Shifter](https://nersc.gitlab.io/development/shifter/how-to-use/)
- `charliecloud`
  - A generic configuration profile to be used with [Charliecloud](https://charliecloud.io/)
- `apptainer`
  - A generic configuration profile to be used with [Apptainer](https://apptainer.org/)
- `wave`
  - A generic configuration profile to enable [Wave](https://seqera.io/wave/) containers. Use together with one of the above (requires Nextflow ` 24.03.0-edge` or later).
- `conda`
  - A generic configuration profile to be used with [Conda](https://conda.io/docs/). Please only use Conda as a last resort i.e. when it's not possible to run the pipeline with Docker, Singularity, Podman, Shifter, Charliecloud, or Apptainer.

### `-resume`

Specify this when restarting a pipeline. Nextflow will use cached results from any pipeline steps where the inputs are the same, continuing from where it got to previously. For input to be considered the same, not only the names must be identical but the files' contents as well. For more info about this parameter, see [this blog post](https://www.nextflow.io/blog/2019/demystifying-nextflow-resume.html).

You can also supply a run name to resume a specific run: `-resume [run-name]`. Use the `nextflow log` command to show previous run names.

### `-c`

Specify the path to a specific config file (this is a core Nextflow command). See the [nf-core website documentation](https://nf-co.re/usage/configuration) for more information.

## Custom configuration

### Resource requests

Each step requests CPUs, memory and time through its nf-core label. A step that runs out of memory or time is retried once with double the memory and time. To change the requests, or cap them at what your machine has, use a `-c` config; [running on a server](setup/servers.md) lists every tool with its label and the thedonkey settings.

### Custom Containers

In some cases, you may wish to change the container or conda environment used by a pipeline steps for a particular tool. By default, nf-core pipelines use containers and software from the [biocontainers](https://biocontainers.pro/) or [bioconda](https://bioconda.github.io/) projects. However, in some cases the pipeline specified version maybe out of date.

To use a different container from the default container or conda environment specified in a pipeline, please see the [updating tool versions](https://nf-co.re/docs/usage/configuration#updating-tool-versions) section of the nf-core website.

### Custom Tool Arguments

A pipeline might not always support every possible argument or option of a particular tool used in pipeline. Fortunately, nf-core pipelines provide some freedom to users to insert additional parameters that the pipeline does not include by default.

To learn how to provide additional arguments to a particular tool of the pipeline, please see the [customising tool arguments](https://nf-co.re/docs/usage/configuration#customising-tool-arguments) section of the nf-core website.

### nf-core/configs

In most cases, you will only need to create a custom config as a one-off but if you and others within your organisation are likely to be running nf-core pipelines regularly and need to use the same settings regularly it may be a good idea to request that your custom config file is uploaded to the `nf-core/configs` git repository. Before you do this please can you test that the config file works with your pipeline of choice using the `-c` parameter. You can then create a pull request to the `nf-core/configs` repository with the addition of your config file, associated documentation file (see examples in [`nf-core/configs/docs`](https://github.com/nf-core/configs/tree/master/docs)), and amending [`nfcore_custom.config`](https://github.com/nf-core/configs/blob/master/nfcore_custom.config) to include your custom profile.

See the main [Nextflow documentation](https://www.nextflow.io/docs/latest/config.html) for more information about creating your own configuration files.

If you have any questions or issues please send us a message on [Slack](https://nf-co.re/join/slack) on the [`#configs` channel](https://nfcore.slack.com/channels/configs).

## Running in the background

Nextflow handles job submissions and supervises the running jobs. The Nextflow process must run until the pipeline is finished.

The Nextflow `-bg` flag launches Nextflow in the background, detached from your terminal so that the workflow does not stop if you log out of your session. The logs are saved to a file.

Alternatively, you can use `screen` / `tmux` or similar tool to create a detached session which you can log back into at a later time.
Some HPC setups also allow you to run nextflow within a cluster job submitted your job scheduler (from where it submits more jobs).

## Nextflow memory requirements

In some cases, the Nextflow Java virtual machines can start to request a large amount of memory.
We recommend adding the following line to your environment to limit this (typically in `~/.bashrc` or `~./bash_profile`):

```bash
NXF_OPTS='-Xms1g -Xmx4g'
```
