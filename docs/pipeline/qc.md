# Quality control

Every isolate gets a `qc_status` of `pass`, `warn` or `fail` and a list of
flags in `qc_summary.tsv`. The thresholds live in
[`assets/qc_thresholds.tsv`](https://github.com/ryanjameskennedy/sinklink/blob/master/assets/qc_thresholds.tsv),
with separate values for Illumina and Nanopore and a severity per check.

| Check | Illumina | Nanopore | Severity | Flag |
|---|---|---|---|---|
| Mean read depth over the assembly | ≥30× | ≥40× | fail | `low_depth` |
| Contigs ≥500 bp (QUAST) | ≤500 | ≤50 | warn | `many_contigs` |
| N50 | ≥15 kb | ≥100 kb | warn | `low_n50` |
| Assembly length inside the schema's expected range | yes | yes | warn | `genome_size` |
| gambitcore completeness | ≥90% | ≥90% | warn | `low_completeness` |
| Bracken fraction of reads from species the schema covers | ≥0.8 | ≥0.8 | fail | `species_mismatch` |
| Largest fraction of reads from a genus outside the schema's genera | ≤0.05 | ≤0.05 | fail | `contamination` |

```{note}
These are starting points, not published cut-offs: adjust them to your lab's
validation. The genome size ranges are approximate.
```

Other flags: `no_assembly` (fail), `no_schema`, `depth_not_measured` and
`species_not_checked` (warn, e.g. when no Kraken2 database was given).

The species and genome size expectations for each schema are the
`species_pattern`, `genera`, `genome_size_min_mb` and `genome_size_max_mb`
columns of `assets/schemas.tsv`, listed on each
[species page](../species/index.md). The species check matters most for the
species complexes: an `enterobacter_cloacae` isolate that Bracken calls
*E. cloacae* rather than *E. hormaechei* fails with `species_mismatch`,
because the scheme only covers *E. hormaechei*.

## Allele calling QC

For cgMLST schemas an isolate also fails with `low_calls` if fewer than 90% of
loci are called (`min_called_fraction` in `assets/schemas.tsv`). The wgMLST
*S. maltophilia* scheme has no such cut-off, since each genome contains only
about a quarter of its loci.

## How QC reaches the pairs

A pair's `qc` column is `fail` if either isolate failed (including
`low_calls`), `warn` if either has warnings, and `not_checked` if no QC summary
was found. Distances are still reported for failed pairs, but should not be
trusted until the isolate is re-sequenced or re-assembled.
