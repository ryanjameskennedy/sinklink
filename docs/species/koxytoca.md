# _Klebsiella oxytoca_ species complex

|             |                                                                                    |
| ----------- | ---------------------------------------------------------------------------------- |
| Schema      | `koxytoca`                                                                         |
| Scheme      | cgmlst.org [Koxytoca_complex](https://www.cgmlst.org/ncs/schema/Koxytoca_complex/) |
| Loci        | 2,536                                                                              |
| Seed genome | NZ_CP033844.1 (used to train Prodigal)                                             |
| Threshold   | ≤6 alleles, borderline ≤9                                                          |
| Lab labels  | `klebsiella_oxytoca`, `klebsiella_oxytoca_group`                                   |

## Threshold

Dabernig-Heinz et al. (2024) built the scheme for the whole monophyletic
_K. oxytoca_ species complex and proposed 6 alleles as a strict and 9 as a
sensitive cut-off. Pairs with 7–9 differences are reported as `borderline`. In
the Graz sink outbreak they describe, an unrelated isolate of the same ST was
only 10 alleles from the cluster.

## Species check

The schema accepts _K. oxytoca_, _K. michiganensis_, _K. grimontii_, _K. pasteurii_, _K. huaxiensis_ and _K. spallanzanii_; reads from _Raoultella_ are not counted as contamination.

| Setting in `assets/schemas.tsv` | Value                  |
| ------------------------------- | ---------------------- | ------------- | --------- | --------- | ---------- | --------------- |
| `species_pattern`               | `^Klebsiella (oxytoca  | michiganensis | grimontii | pasteurii | huaxiensis | spallanzanii)$` |
| `genera`                        | Klebsiella, Raoultella |
| Expected genome size            | 5.5–6.8 Mb             |

## In the VASK study

Transmission_4 (357 days) and Transmission_5 (3 days, same patient).

## Notes

- _K. oxytoca_ is often confused with _K. michiganensis_ and _K. grimontii_ by
  MALDI-TOF; the scheme covers all of them, so the lab label matters less than
  for other species.
- The two lab labels ("oxytoca" and "oxytoca group") map to the same schema.

Full citations are in the [references](../reference/references.md).
