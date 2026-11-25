# _Serratia marcescens_

|                  |                                                                                                                                       |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Schema           | `smarcescens`                                                                                                                         |
| Scheme           | cgmlst.org [Smarcescens](https://www.cgmlst.org/ncs/schema/Smarcescens/)                                                              |
| Loci             | 2,692                                                                                                                                 |
| Seed genome      | NZ_HG326223.1 (used to train Prodigal)                                                                                                |
| Reference genome | [GCF_030291735.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_030291735.1/) (ELP1.10) (used for QUAST, Mash and variant calling) |
| Threshold        | ≤12 alleles                                                                                                                           |
| Lab labels       | `serratia_marcescens`                                                                                                                 |

## Threshold

The complex type distance listed on cgmlst.org for this scheme, which was
described by Kampmeier et al. (2022). An earlier wgMLST scheme (9,377 loci)
used ≤20 alleles, with most outbreak isolates ≤4 apart.

## Species check

The schema accepts the species of the _S. marcescens_ complex: _S. marcescens_,
_S. nematodiphila_, _S. ureilytica_, _S. sarumanii_, _S. bockelmannii_,
_S. nevei_ and _S. montpellierensis_.

| Setting in `assets/schemas.tsv` | Value                                                                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `species_pattern`               | `^Serratia (marcescens\|nematodiphila\|ureilytica\|sarumanii\|bockelmannii\|nevei\|montpellierensis)$` |
| `genera`                        | Serratia                                                                                               |
| Expected genome size            | 4.8–5.8 Mb                                                                                             |
| `mlst_scheme`                   | `serratia`                                                                                             |

## In the VASK study

Transmission_7 (50 days, three patients).

## Notes

- NICU outbreaks reported as _S. marcescens_ have turned out to involve
  _S. sarumanii_ and _S. bockelmannii_. These and the other species of the
  _S. marcescens_ complex with a type strain in `assets/type_strains.tsv` pass
  the species check, since Kraken2 cannot tell them apart; the species call
  names them.
- The cgmlst.org download can be slow; see [schemas](../setup/schemas.md) if it
  fails.

Full citations are in the [references](../reference/references.md).
