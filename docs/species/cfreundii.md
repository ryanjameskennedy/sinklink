# _Citrobacter freundii_

|                  |                                                                                                                                       |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Schema           | `cfreundii`                                                                                                                           |
| Scheme           | cgmlst.org [Cfreundii](https://www.cgmlst.org/ncs/schema/Cfreundii/)                                                                  |
| Loci             | 3,250                                                                                                                                 |
| Seed genome      | NZ_CP049015.1 (used to train Prodigal)                                                                                                |
| Reference genome | [GCF_904859905.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_904859905.1/) (MSB1_1H) (used for QUAST, Mash and variant calling) |
| Threshold        | ≤10 alleles                                                                                                                           |
| Lab labels       | `citrobacter_freundii`                                                                                                                |

## Threshold

The complex type distance listed on cgmlst.org for this scheme, which was
described and validated by Kieninger et al. (2025).

## Species check

The schema accepts _C. freundii_.

| Setting in `assets/schemas.tsv` | Value                    |
| ------------------------------- | ------------------------ |
| `species_pattern`               | `^Citrobacter freundii$` |
| `genera`                        | Citrobacter              |
| Expected genome size            | 4.7–5.9 Mb               |

## In the VASK study

Transmission_6 (3 days, same patient; sink and airway sampled on the same day).

## Notes

- Carbapenemase-producing _C. freundii_ clones have persisted in hospital
  plumbing for years (Hamerlinck et al. 2023).
- Other members of the _C. freundii_ complex fail the species check.

Full citations are in the [references](../reference/references.md).
