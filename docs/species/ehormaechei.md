# _Enterobacter hormaechei_

|                  |                                                                                                                                             |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Schema           | `ehormaechei`                                                                                                                               |
| Scheme           | cgmlst.org [Ehormaechei](https://www.cgmlst.org/ncs/schema/Ehormaechei/)                                                                    |
| Loci             | 2,178                                                                                                                                       |
| Seed genome      | NZ_CP100388.1 (used to train Prodigal)                                                                                                      |
| Reference genome | [GCF_019048245.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_019048245.1/) (FDAARGOS 1433) (used for QUAST, Mash and variant calling) |
| Threshold        | ≤12 alleles                                                                                                                                 |
| Lab labels       | `enterobacter_cloacae`, `enterobacter_cloacae_complex`                                                                                      |

## Threshold

The complex type distance listed on cgmlst.org for this scheme, which was
published with Prior et al. (2025).

## Species check

The schema accepts _E. hormaechei_ only.

| Setting in `assets/schemas.tsv` | Value                       |
| ------------------------------- | --------------------------- |
| `species_pattern`               | `^Enterobacter hormaechei$` |
| `genera`                        | Enterobacter                |
| Expected genome size            | 4.4–5.4 Mb                  |

## In the VASK study

Transmission_1 (59 days).

## Notes

- There is no cgmlst.org scheme for the whole _E. cloacae_ complex, only for
  _E. hormaechei_. Isolates labelled _E. cloacae_ are run against it, which is
  only valid once the genome confirms _E. hormaechei_: an isolate that Bracken
  calls _E. cloacae_ or _E. asburiae_ fails with `species_mismatch`.
- A 2026 preprint describing an _E. cloacae_ complex cgMLST found
  epidemiologically linked isolates 0–3 alleles apart.

Full citations are in the [references](../reference/references.md).
