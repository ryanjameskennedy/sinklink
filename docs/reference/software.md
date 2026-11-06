# Software

The pipeline uses the container each nf-core module pins; the versions below
are those of the installed modules (recorded in `modules.json`). chewBBACA is
the exception: its container is pinned to 3.5.4 in `conf/modules.config` so
allele calling uses the same version that prepared the schemas.

```{csv-table} Tools and versions
:file: software.csv
:header-rows: 1
```

The exact versions used in a run are written to
`pipeline_info/sinklink_software_mqc_versions.yml` and shown in the MultiQC
report. Update the modules with `nf-core modules update`.

Tool citations are in
[`CITATIONS.md`](https://github.com/ryanjameskennedy/sinklink/blob/master/CITATIONS.md).
