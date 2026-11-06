# Interpreting the results

## Pair verdicts

`summary/pairwise_distances.tsv` has one row per pair of isolates in the same
transmission group.

| Verdict | Meaning |
|---|---|
| `within_threshold` | At or below the species threshold: same strain |
| `borderline` | Between the strict and sensitive thresholds (*K. oxytoca* only) |
| `above_threshold` | Above the threshold: not the same strain |
| `missing_profile` | One or both isolates have no allele profile |
| `different_schema` | The two isolates were typed with different schemas |

Allele calls are counted only when both isolates have a valid allele at a
locus. Missing or ambiguous calls (`LNF`, `PLOT3`, `PLOT5`, `ASM`, `ALM`,
`NIPH`, `NIPHEM`, `LOTSC`, `PAMA`) are ignored rather than counted as
differences. Novel alleles keep their `*` prefix so they never match a schema
allele with the same number.

The `notes` column lists QC flags of either isolate, different 7-gene STs and
pairs sequenced on different platforms.

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
source. Check borderline pairs with SNPs (e.g. SKA2 or Snippy).

See also the [caveats](caveats.md).
