# Quality control

Every isolate gets a `qc_status` of `pass`, `warn` or `fail` and a list of
flags in `qc_summary.tsv`. The thresholds live in
[`assets/qc_thresholds.tsv`](https://github.com/ryanjameskennedy/sinklink/blob/master/assets/qc_thresholds.tsv),
with separate values for Illumina and Nanopore and a severity per check.

| Check                                                              | Illumina | Nanopore | Severity | Flag                |
| ------------------------------------------------------------------ | -------- | -------- | -------- | ------------------- |
| Mean read depth over the assembly                                  | ≥30×     | ≥40×     | fail     | `low_depth`         |
| Contigs ≥500 bp (QUAST)                                            | ≤500     | ≤50      | warn     | `many_contigs`      |
| N50                                                                | ≥15 kb   | ≥100 kb  | warn     | `low_n50`           |
| Assembly length inside the schema's expected range                 | yes      | yes      | warn     | `genome_size`       |
| gambitcore completeness                                            | ≥90%     | ≥90%     | warn     | `low_completeness`  |
| Mash distance from the assembly to the schema's reference genome   | ≤0.05    | ≤0.05    | warn     | `distant_reference` |
| Bracken fraction of reads from species the schema covers           | ≥0.8     | ≥0.8     | fail     | `species_mismatch`  |
| Largest fraction of reads from a genus outside the schema's genera | ≤0.05    | ≤0.05    | fail     | `contamination`     |

```{note}
These are starting points, not published cut-offs: adjust them to your lab's
validation. The genome size ranges are approximate.
```

Other flags: `no_assembly` (fail), `no_schema`, `depth_not_measured` and
`species_not_checked` (warn, e.g. when Kraken2 classified no reads to species).

The QC summary also reports, without a threshold, the reference genome
accession, the Mash distance and QUAST's genome fraction (the share of the
reference genome covered by the assembly). A Mash distance of 0.05 is roughly
95% average nucleotide identity, the usual species boundary; isolates further
from the reference have more of their genome unmapped, so their variant calls
and SNP distances cover less of the genome.

The species and genome size expectations for each schema are the
`species_pattern`, `genera`, `genome_size_min_mb` and `genome_size_max_mb`
columns of `assets/schemas.tsv`, listed on each
[species page](../species/index.md). The species check matters most for the
species complexes: an `enterobacter_cloacae` isolate that Bracken calls
_E. cloacae_ rather than _E. hormaechei_ fails with `species_mismatch`,
because the scheme only covers _E. hormaechei_.

## Allele calling QC

For cgMLST schemas an isolate also fails with `low_calls` if fewer than 90% of
loci are called (`min_called_fraction` in `assets/schemas.tsv`). The wgMLST
_S. maltophilia_ scheme has no such cut-off, since each genome contains only
about a quarter of its loci.

## How QC reaches the pairs

A pair's `qc` column is `fail` if either isolate failed (including
`low_calls`), `warn` if either has warnings, and `not_checked` if no QC summary
was found. Distances are still reported for failed pairs, but should not be
trusted until the isolate is re-sequenced or re-assembled.
