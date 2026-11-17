# _Klebsiella pneumoniae_ species complex

|                  |                                                                                                                                       |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Schema           | `kpneumoniae`                                                                                                                         |
| Scheme           | cgmlst.org [Kpneumoniae_complex](https://www.cgmlst.org/ncs/schema/Kpneumoniae_complex/)                                              |
| Loci             | 2,358                                                                                                                                 |
| Seed genome      | NC_012731.1 (used to train Prodigal)                                                                                                  |
| Reference genome | [GCF_000240185.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_000240185.1/) (HS11286) (used for QUAST, Mash and variant calling) |
| Threshold        | ≤15 alleles                                                                                                                           |
| Lab labels       | `klebsiella_pneumoniae`                                                                                                               |

## Threshold

The complex type distance listed on cgmlst.org for this scheme. For SNP
typing, ≤21 SNPs has been used to define nosocomial transmission in Europe
(David et al. 2019).

## Species check

The schema accepts _K. pneumoniae_, _K. quasipneumoniae_, _K. variicola_, _K. quasivariicola_ and _K. africana_.

| Setting in `assets/schemas.tsv` | Value                                                                             |
| ------------------------------- | --------------------------------------------------------------------------------- |
| `species_pattern`               | `^Klebsiella (pneumoniae\|quasipneumoniae\|variicola\|quasivariicola\|africana)$` |
| `genera`                        | Klebsiella                                                                        |
| Expected genome size            | 5.0–6.5 Mb                                                                        |
| `mlst_scheme`                   | `klebsiella`                                                                      |

## In the VASK study

Transmission_9 (68 days; sink and airway sampled on the same day).

## Notes

- The reference is _K. pneumoniae_ HS11286. Isolates of the other species in the complex (_K. quasipneumoniae_, _K. variicola_) sit further from it, so less of their genome is compared in the SNP distances; check `reference_distance` in the QC summary.
- Same-day sink and airway samples fit spread in either direction.

Full citations are in the [references](../reference/references.md).
