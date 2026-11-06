# *Serratia marcescens*

| | |
|---|---|
| Schema | `smarcescens` |
| Scheme | cgmlst.org [Smarcescens](https://www.cgmlst.org/ncs/schema/Smarcescens/) |
| Loci | 2,692 |
| Seed genome | NZ_HG326223.1 (used to train Prodigal) |
| Threshold | ≤12 alleles |
| Lab labels | `serratia_marcescens` |

## Threshold

The complex type distance listed on cgmlst.org for this scheme, which was
described by Kampmeier et al. (2022). An earlier wgMLST scheme (9,377 loci)
used ≤20 alleles, with most outbreak isolates ≤4 apart.

## Species check

The schema accepts *S. marcescens* and *S. nematodiphila*.

| Setting in `assets/schemas.tsv` | Value |
|---|---|
| `species_pattern` | `^Serratia (marcescens|nematodiphila)$` |
| `genera` | Serratia |
| Expected genome size | 4.8–5.8 Mb |

## In the VASK study

Transmission_7 (50 days, three patients).

## Notes

- NICU outbreaks reported as *S. marcescens* have turned out to involve
  *S. sarumanii* and *S. bockelmannii*; these fail the species check.
- The cgmlst.org download can be slow; see [schemas](../setup/schemas.md) if it
  fails.

Full citations are in the [references](../reference/references.md).
