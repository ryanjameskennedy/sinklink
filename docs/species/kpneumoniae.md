# *Klebsiella pneumoniae* species complex

| | |
|---|---|
| Schema | `kpneumoniae` |
| Scheme | cgmlst.org [Kpneumoniae_complex](https://www.cgmlst.org/ncs/schema/Kpneumoniae_complex/) |
| Loci | 2,358 |
| Seed genome | NC_012731.1 (used to train Prodigal) |
| Threshold | ≤15 alleles |
| Lab labels | `klebsiella_pneumoniae` |

## Threshold

The complex type distance listed on cgmlst.org for this scheme. For SNP
typing, ≤21 SNPs has been used to define nosocomial transmission in Europe
(David et al. 2019).

## Species check

The schema accepts *K. pneumoniae*, *K. quasipneumoniae*, *K. variicola*, *K. quasivariicola* and *K. africana*.

| Setting in `assets/schemas.tsv` | Value |
|---|---|
| `species_pattern` | `^Klebsiella (pneumoniae|quasipneumoniae|variicola|quasivariicola|africana)$` |
| `genera` | Klebsiella |
| Expected genome size | 5.0–6.5 Mb |

## In the VASK study

Transmission_9 (68 days; sink and airway sampled on the same day).

## Notes

- Same-day sink and airway samples fit spread in either direction.

Full citations are in the [references](../reference/references.md).
