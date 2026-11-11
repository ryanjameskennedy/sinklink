# Contributing

sinklink follows the nf-core pipeline layout:

```text
main.nf                     entry point
workflows/sinklink.nf       main workflow
subworkflows/local/         read_preparation, assembly, assembly_qc, species_check,
                            variant_calling, allele_calling, utils_nfcore_sinklink_pipeline
modules/nf-core/            installed nf-core modules (modules.json)
modules/local/              gambitcore, summarise_qc, check_distances, transmission_report
conf/                       base, modules, test and test_full configs
assets/                     schemas.tsv, species_map.tsv, qc_thresholds.tsv, samplesheet schema, test inputs
bin/                        summarise_qc.py, check_distances.py, split_alleles.py, transmission_report.py
assets/awk/                 gawk programs for the masks, pseudogenomes and alignments
docs/                       this documentation (Sphinx + MyST)
Makefile, containers/       schema and database setup
```

## Checks

Before opening a pull request:

```bash
pre-commit run --all-files
nf-core pipelines lint
nf-test test --profile +docker
pip install -r docs/requirements.txt && sphinx-build -W -b html docs docs/_build/html
```

The nf-test tests in `tests/default.nf.test` stub-run the `test` profile, once
with the defaults and once with every optional step, and compare the output file
names and contents with the snapshot in `tests/default.nf.test.snap` (tool
versions are left out). After an intended change in the outputs, update it with
`nf-test test --profile +docker --update-snapshot`.

GitHub Actions on pull requests (the nf-core template workflows):

- `linting.yml`: pre-commit (prettier, whitespace) and `nf-core pipelines lint`;
- `nf-test.yml`: the nf-test tests with Docker, and with Singularity on pull
  requests to `master`, on Nextflow 25.04.0;
- `download_pipeline.yml`: `nf-core pipelines download` of the pull request's
  branch with its Singularity images, then a stub run of the downloaded copy;
- `branch.yml`: pull requests to `master` must come from `dev`, a `release/*`
  branch or a branch named `patch`;
- `docs.yml`: the strict docs build.

The template's version comment workflow is removed: it needs the nf-core bot's
token, so it could only fail here.

## Pipeline diagram

The metro map in the README and these docs is drawn with
[nf-metro](https://github.com/seqeralabs/nf-metro) from `assets/metro_map.mmd`.
After a change to the steps, update that file and redraw both images:

```bash
pip install nf-metro
nf-metro render assets/metro_map.mmd -o docs/images/metro_map.svg
nf-metro render assets/metro_map.mmd --mode light -o docs/images/metro_map_light.png
```

## Modules

Install or update nf-core modules with `nf-core modules install <tool>` and
`nf-core modules update`; tool options belong in `conf/modules.config`, not in
the module files. New parameters go in both `nextflow.config` and
`nextflow_schema.json`.

## Releases

Bump the version with `nf-core pipelines bump-version <version>`, add a
`CHANGELOG.md` entry, and tag the release as `v<version>`.
