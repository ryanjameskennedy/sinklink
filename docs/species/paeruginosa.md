# _Pseudomonas aeruginosa_

|             |                                                                          |
| ----------- | ------------------------------------------------------------------------ |
| Schema      | `paeruginosa`                                                            |
| Scheme      | cgmlst.org [Paeruginosa](https://www.cgmlst.org/ncs/schema/Paeruginosa/) |
| Loci        | 3,867                                                                    |
| Seed genome | NC_002516.2 (PAO1) (used to train Prodigal)                              |
| Threshold   | ≤12 alleles                                                              |
| Lab labels  | `pseudomonas_aeruginosa`                                                 |

## Threshold

The complex type distance listed on cgmlst.org for this scheme. The paper
describing the scheme (Tönnies et al. 2021) evaluates it against SNP typing but
does not itself state a cut-off.

## Species check

The schema accepts _P. aeruginosa_.

| Setting in `assets/schemas.tsv` | Value                      |
| ------------------------------- | -------------------------- |
| `species_pattern`               | `^Pseudomonas aeruginosa$` |
| `genera`                        | Pseudomonas                |
| Expected genome size            | 5.5–7.8 Mb                 |

## In the VASK study

Transmission_3 (338 days) and Transmission_8 (60 days).

## Notes

- Transmission_3 spans almost a year, so expect more differences than in a
  short outbreak even from a single persisting source (Duval, Opatowski &
  Brisse 2023).

Full citations are in the [references](../reference/references.md).
