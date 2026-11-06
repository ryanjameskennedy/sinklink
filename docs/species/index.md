# Species and thresholds

Each species is typed with its own scheme and compared against its own
allele-difference threshold. A pair is `within_threshold` when its allele
differences are at or below the threshold. The values live in
[`assets/schemas.tsv`](https://github.com/ryanjameskennedy/sinklink/blob/master/assets/schemas.tsv).

## Where each threshold comes from

The source of the threshold is not always the paper that describes the scheme,
so both are listed.

| Species | Schema | Scheme (loci) | Threshold (alleles) | Threshold from | Scheme described in |
|---|---|---|---|---|---|
| [*Pseudomonas aeruginosa*](paeruginosa.md) | `paeruginosa` | cgmlst.org Paeruginosa (3,867) | ≤12 | cgmlst.org complex type distance | Tönnies et al. 2021 |
| [*Klebsiella pneumoniae* species complex](kpneumoniae.md) | `kpneumoniae` | cgmlst.org Kpneumoniae_complex (2,358) | ≤15 | cgmlst.org complex type distance | cgmlst.org |
| [*Klebsiella oxytoca* species complex](koxytoca.md) | `koxytoca` | cgmlst.org Koxytoca_complex (2,536) | ≤6 (borderline ≤9) | Dabernig-Heinz et al. 2024 | Dabernig-Heinz et al. 2024 |
| [*Serratia marcescens*](smarcescens.md) | `smarcescens` | cgmlst.org Smarcescens (2,692) | ≤12 | cgmlst.org complex type distance | Kampmeier et al. 2022 |
| [*Citrobacter freundii*](cfreundii.md) | `cfreundii` | cgmlst.org Cfreundii (3,250) | ≤10 | cgmlst.org complex type distance | Kieninger et al. 2025 |
| [*Enterobacter hormaechei*](ehormaechei.md) | `ehormaechei` | cgmlst.org Ehormaechei (2,178) | ≤12 | cgmlst.org complex type distance | Prior et al. 2025 |
| [*Stenotrophomonas maltophilia* complex](smaltophilia.md) | `smaltophilia` | Gröschel 2020 wgMLST (17,603) | ≤10 | Gröschel et al. 2020 (d10) | Gröschel et al. 2020 |

Only the *K. oxytoca* and *S. maltophilia* thresholds come from a paper that
tested them on isolates; the cgmlst.org values are the complex type distances
the scheme authors publish with each scheme. Treat them all as guides: see
[caveats](../results/caveats.md).

## From laboratory label to schema

The `growth` column of the metadata is mapped to a schema by
[`assets/species_map.tsv`](https://github.com/ryanjameskennedy/sinklink/blob/master/assets/species_map.tsv):

| `growth` | Schema |
|---|---|
| `pseudomonas_aeruginosa` | `paeruginosa` |
| `klebsiella_pneumoniae` | `kpneumoniae` |
| `klebsiella_oxytoca`, `klebsiella_oxytoca_group` | `koxytoca` |
| `serratia_marcescens` | `smarcescens` |
| `citrobacter_freundii` | `cfreundii` |
| `enterobacter_cloacae`, `enterobacter_cloacae_complex` | `ehormaechei` (only valid once the genome confirms *E. hormaechei*) |
| `stenotrophomonas_maltophilia` | `smaltophilia` |

The match is exact. An isolate whose label is not in the table is assembled and
QC'd but not allele called.

## Species checks

The laboratory label is not trusted on its own: Kraken2/Bracken must assign at
least 80% of the reads to species the schema covers (`species_pattern`), and no
other genus may exceed 5% (see [quality control](../pipeline/qc.md)). Each
species page lists what its schema accepts.

## Adding a species

1. Add the schema to the `SCHEMAS` list in the `Makefile` with its download
   URL, archive name and seed genome, and run `make <schema>_all`.
2. Add a row to `assets/schemas.tsv` with the threshold, the accepted species,
   genera and genome size range, and the source.
3. Map the laboratory labels to it in `assets/species_map.tsv`.
4. Add a page here.

```{toctree}
:hidden:
:maxdepth: 1

paeruginosa
kpneumoniae
koxytoca
smarcescens
cfreundii
ehormaechei
smaltophilia
```
