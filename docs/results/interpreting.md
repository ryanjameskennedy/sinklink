# Interpreting the results

## Pair verdicts

`summary/pairwise_distances.tsv` has one row per pair of isolates in the same
transmission group.

| Verdict | Meaning |
|---|---|
| `within_threshold` | At or below the species threshold ([cut-offs](../species/index.md)): same strain, consistent with the same colonisation |
| `borderline` | Between the strict and sensitive thresholds (*K. oxytoca* only) |
| `above_threshold` | Above the threshold: different strains, not the same colonisation |
| `missing_profile` | One or both isolates have no allele profile |
| `different_schema` | The two isolates were typed with different schemas |

Allele calls are counted only when both isolates have a valid allele at a
locus. Missing or ambiguous calls (`LNF`, `PLOT3`, `PLOT5`, `ASM`, `ALM`,
`NIPH`, `NIPHEM`, `LOTSC`, `PAMA`) are ignored rather than counted as
differences. Novel alleles keep their `*` prefix so they never match a schema
allele with the same number.

The `notes` column lists QC flags of either isolate, different 7-gene STs and
pairs sequenced on different platforms.

## SNP distances

When both isolates were variant called against their schema's reference
genome, `snp_distance` counts the chromosome positions where both have a base
and the bases differ. Positions with too few reads (below `--snp_min_depth`)
in either isolate, and the reference's repeats and prophages, are left out, as
are indels. `snp_recombination_filtered` is `yes` when Gubbins removed SNPs in
recombinant regions first; it needs 3 or more sequences in the schema's
alignment (the reference counts as one), so a schema with a single isolate
pair gets `no`.

SNP distances have no threshold and do not change the verdict. Use them to
check a pair near the allele threshold, or a `borderline` _K. oxytoca_ pair:
a pair within the allele threshold but many SNPs apart deserves a closer look,
and so does one with few SNPs but many allele differences. Isolates far from
the reference (see `reference_distance` in the QC summary) have less of their
genome compared, so their SNP distance covers only the part they share with
the reference.

## Group summaries

`summary/group_summary.tsv` gives each group one of `all_pairs_within`,
`some_pairs_within`, `no_pairs_within`, `incomplete` (profiles missing) or
`single_isolate`, with the worst pair QC.

## Reading a pair

1. **Did both isolates pass QC?** If not, fix that first
   ([quality control](../pipeline/qc.md)).
2. **Same species and lineage (same 7-gene ST)?** If not, no link.
3. **Within the threshold?** Then the isolates are **genomically linked**.
4. **Do the dates and room support the sink as the source** (sink positive
   first, patient negative on admission)? Only then call it **probable
   sink-to-patient transmission**. Same-day samples or a patient positive
   before the sink fit patient-to-sink spread equally well.

For groups spanning months (in VASK, Transmission_3 and Transmission_4), expect
more differences than in a short outbreak even from a single persisting
source. Check borderline pairs against their SNP distance.

See also the [caveats](caveats.md).

## Transmission report

`report/transmission_report.html` puts the tables and figures together. Some
things to keep in mind when reading the figures:

- **Distance overview and distance against time.** Each mark is a pair. Filled
  orange marks are within the threshold, blue ones borderline and hollow grey
  ones above it. A diamond joins an environmental sample to a patient sample,
  a square two environmental samples and a circle two patient samples. Above
  20 allele differences the axis is logarithmic, so unrelated pairs fit
  alongside the close ones.
- **Timelines.** Each isolate is joined to the earlier isolate it is closest to,
  when that pair is within the threshold. The line shows the closest earlier
  match, not a proven direction of spread: an unsampled source, or a sink and a
  patient both seeded from elsewhere, give the same picture.
- **Minimum spanning trees.** Built from the pairwise allele differences, each
  over the loci both isolates share. When several trees are equally short only
  one is drawn, and missing loci can shorten links, so use the trees to see the
  structure of a group and the pair table for the numbers.
- **Allele against SNP distance.** The two methods should rise together. A
  pair that is close by alleles but far by SNPs, or the other way round, is
  worth checking in the pair table and the QC.
