# Quality control

Every isolate gets a `qc_status` of `pass`, `warn` or `fail` and a list of
flags in `qc_summary.tsv`. The thresholds live in
[`assets/qc_thresholds.tsv`](https://github.com/ryanjameskennedy/sinklink/blob/master/assets/qc_thresholds.tsv),
with separate values for Illumina and Nanopore and a severity per check.

| Check                                                              | Illumina | Nanopore | Severity | Flag                |
| ------------------------------------------------------------------ | -------- | -------- | -------- | ------------------- |
| Mean read depth over the assembly                                  | ≥30×     | ≥40×     | fail     | `low_depth`         |
| Share of reads that map back to the assembly                       | ≥0.9     | ≥0.9     | warn     | `low_mapped_reads`  |
| Contigs ≥500 bp (QUAST)                                            | ≤500     | ≤50      | warn     | `many_contigs`      |
| N50                                                                | ≥15 kb   | ≥100 kb  | warn     | `low_n50`           |
| Assembly length inside the schema's expected range                 | yes      | yes      | warn     | `genome_size`       |
| gambitcore completeness                                            | ≥90%     | ≥90%     | warn     | `low_completeness`  |
| skani ANI from the assembly to the schema's reference genome       | ≥95%     | ≥95%     | warn     | `distant_reference` |
| Bracken fraction of reads from species the schema covers           | ≥0.8     | ≥0.8     | fail     | `species_mismatch`  |
| Largest fraction of reads from a genus outside the schema's genera | ≤0.05    | ≤0.05    | fail     | `contamination`     |

```{note}
These are starting points, not published cut-offs: adjust them to your lab's
validation. The genome size ranges are approximate.
```

Other flags: `no_assembly` (fail), `no_schema`, `depth_not_measured` and
`species_not_checked` (warn, e.g. when Kraken2 classified no reads to species).

The QC summary also reports, without a threshold, the number of reads, the
breadth (the share of the assembly covered by at least one read), the reference
genome accession, the share of the assembly skani aligned to it, the Mash
distance and QUAST's genome fraction (the share of the reference genome covered
by the assembly).

## Depth, reads and mapping

Depth, reads, mapped reads and breadth come from mapping each isolate's reads
back to its own assembly (`bwa mem` or `minimap2`, then `samtools coverage` and
`samtools flagstat`). Depth is the mean number of reads covering each base of
the assembly, weighted by contig length: the usual "coverage" figure, such as
50×. Mapping to the isolate's own assembly measures the sequencing itself,
whatever the species: every part of the genome that was assembled can be
counted, and reads that don't map back point to contamination, host reads or a
poor assembly. Mapping to the reference instead mixes sequencing depth with how
far the isolate is from the reference, since genes the reference lacks get no
reads; that is measured separately by the ANI and genome fraction, and the
variant calling track reports its own depth against the reference with
mosdepth.

There is no read count threshold: depth already accounts for the number and
length of the reads relative to the genome, and an isolate with too few reads
fails `low_depth`. Low N50 and many contigs are warnings, since a fragmented
assembly mostly costs allele calls at contig ends, which the allele calling QC
below catches.

## ANI to the reference

skani ([Shaw & Yu 2023](https://doi.org/10.1038/s41592-023-02018-3)) estimates
the average nucleotide identity (ANI) between the assembly and the schema's
reference genome. 95% ANI is the usual species boundary. skani is accurate on
fragmented draft assemblies and reports the aligned fraction alongside the ANI;
it reports nothing below about 80% ANI, which is flagged as `ANI<80%`. Without
an ANI (e.g. no reference genome), the Mash distance is checked instead
(≤0.05, roughly 95% ANI). Isolates further from the reference have more of
their genome unmapped, so their variant calls and SNP distances cover less of
the genome.

The species and genome size expectations for each schema are the
`species_pattern`, `genera`, `genome_size_min_mb` and `genome_size_max_mb`
columns of `assets/schemas.tsv`, listed on each
[species page](../species/index.md). The species check matters most for the
species complexes: an `enterobacter_hormaechei` isolate that Bracken calls
_E. cloacae_ fails with `species_mismatch`, because that scheme only covers
_E. hormaechei_. Isolates labelled _E. cloacae_ (complex) use the scheme for the
whole complex instead, where an _E. hormaechei_ isolate passes the species
check but gets a `distant_reference` warning, the reference being
_E. cloacae_.

## Allele calling QC

For cgMLST schemas an isolate also fails with `low_calls` if fewer than 90% of
loci are called (`min_called_fraction` in `assets/schemas.tsv`). The wgMLST
_S. maltophilia_ scheme has no such cut-off, since each genome contains only
about a quarter of its loci.

`allele_qc.tsv` lists, per isolate, the loci called, the missing loci (schema
loci without a valid call: not found, partial at a contig end, or ambiguous)
and the novel alleles (calls not yet in the schema, inferred in this run). A
few novel alleles per isolate are normal. Dozens to hundreds in one isolate
usually mean sequencing or assembly errors, such as Nanopore indels, rather
than real differences, and each one can add an allele difference to every pair
the isolate is in. The transmission report shows both counts for every isolate.

## How QC reaches the pairs

A pair's `qc` column is `fail` if either isolate failed (including
`low_calls`), `warn` if either has warnings, and `not_checked` if no QC summary
was found. Distances are still reported for failed pairs, but should not be
trusted until the isolate is re-sequenced or re-assembled.
