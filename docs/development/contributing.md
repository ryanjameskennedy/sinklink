# Contributing

sinklink follows the nf-core pipeline layout:

```text
main.nf                     entry point
workflows/sinklink.nf       main workflow
subworkflows/local/         read_preparation, assembly, assembly_qc,
                            species_check, allele_calling, utils_nfcore_sinklink_pipeline
modules/nf-core/            installed nf-core modules (modules.json)
modules/local/              gambitcore, summarise_qc, check_distances
conf/                       base, modules and test configs
assets/                     schemas.tsv, species_map.tsv, qc_thresholds.tsv, samplesheet schema, test inputs
bin/                        summarise_qc.py, check_distances.py, split_alleles.py
docs/                       this documentation (Sphinx + MyST)
Makefile, containers/       schema and database setup
```

## Checks

Before opening a pull request:

```bash
nf-core pipelines lint
nextflow run . -profile test,docker -stub --outdir results
pip install -r docs/requirements.txt && sphinx-build -W -b html docs docs/_build/html
```

GitHub Actions runs the stub test and builds the docs on every push and pull
request.

## Modules

Install or update nf-core modules with `nf-core modules install <tool>` and
`nf-core modules update`; tool options belong in `conf/modules.config`, not in
the module files. New parameters go in both `nextflow.config` and
`nextflow_schema.json`.

## Releases

Bump the version with `nf-core pipelines bump-version <version>`, add a
`CHANGELOG.md` entry, and tag the release as `v<version>`.
