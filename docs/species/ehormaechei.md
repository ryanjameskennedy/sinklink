# *Enterobacter hormaechei*

| | |
|---|---|
| Schema | `ehormaechei` |
| Scheme | cgmlst.org [Ehormaechei](https://www.cgmlst.org/ncs/schema/Ehormaechei/) |
| Loci | 2,178 |
| Seed genome | NZ_CP100388.1 (used to train Prodigal) |
| Threshold | ≤12 alleles |
| Lab labels | `enterobacter_cloacae`, `enterobacter_cloacae_complex` |

## Threshold

The complex type distance listed on cgmlst.org for this scheme, which was
published with Prior et al. (2025).

## Species check

The schema accepts *E. hormaechei* only.

| Setting in `assets/schemas.tsv` | Value |
|---|---|
| `species_pattern` | `^Enterobacter hormaechei$` |
| `genera` | Enterobacter |
| Expected genome size | 4.4–5.4 Mb |

## In the VASK study

Transmission_1 (59 days).

## Notes

- There is no cgmlst.org scheme for the whole *E. cloacae* complex, only for
  *E. hormaechei*. Isolates labelled *E. cloacae* are run against it, which is
  only valid once the genome confirms *E. hormaechei*: an isolate that Bracken
  calls *E. cloacae* or *E. asburiae* fails with `species_mismatch`.
- A 2026 preprint describing an *E. cloacae* complex cgMLST found
  epidemiologically linked isolates 0–3 alleles apart.

Full citations are in the [references](../reference/references.md).
