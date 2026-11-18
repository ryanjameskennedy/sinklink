# Species and thresholds

Each species is typed with its own scheme and compared against its own
allele-difference threshold. The allele difference of a pair is the number of
loci where both isolates have a valid chewBBACA call and the calls differ;
loci missing in either isolate are not counted.

- **At or below the threshold** (`within_threshold`): the two isolates are
  classed as the same strain, the genomic requirement for calling them the same
  colonisation. The sampling dates and patient history then decide whether the
  link is plausible (see [interpreting the results](../results/interpreting.md)).
- **Above the threshold** (`above_threshold`): different strains, so not the
  same colonisation.
- **_K. oxytoca_ and the _E. cloacae_ complex only**: 7–9 and 4–5 differences
  are `borderline`; check these with SNPs.

The values live in
[`assets/schemas.tsv`](https://github.com/ryanjameskennedy/sinklink/blob/master/assets/schemas.tsv).

## Where each threshold comes from

The source of the threshold is not always the paper that describes the scheme,
so both are listed.

| Species                                                   | Schema         | Scheme (loci)                          | Threshold (alleles) | Threshold from                                                                             | Scheme described in                                                              |
| --------------------------------------------------------- | -------------- | -------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| [_Pseudomonas aeruginosa_](paeruginosa.md)                | `paeruginosa`  | cgmlst.org Paeruginosa (3,867)         | ≤12                 | [cgmlst.org complex type distance](https://www.cgmlst.org/ncs/schema/Paeruginosa/)         | [Tönnies et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8106710/)         |
| [_Klebsiella pneumoniae_ species complex](kpneumoniae.md) | `kpneumoniae`  | cgmlst.org Kpneumoniae_complex (2,358) | ≤15                 | [cgmlst.org complex type distance](https://www.cgmlst.org/ncs/schema/Kpneumoniae_complex/) | [cgmlst.org](https://www.cgmlst.org/ncs/schema/Kpneumoniae_complex/)             |
| [_Klebsiella oxytoca_ species complex](koxytoca.md)       | `koxytoca`     | cgmlst.org Koxytoca_complex (2,536)    | ≤6 (borderline ≤9)  | [Dabernig-Heinz et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11237601/)           | [Dabernig-Heinz et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11237601/) |
| [_Serratia marcescens_](smarcescens.md)                   | `smarcescens`  | cgmlst.org Smarcescens (2,692)         | ≤12                 | [cgmlst.org complex type distance](https://www.cgmlst.org/ncs/schema/Smarcescens/)         | [Kampmeier et al. 2022](https://doi.org/10.1128/jcm.01196-22)                    |
| [_Citrobacter freundii_](cfreundii.md)                    | `cfreundii`    | cgmlst.org Cfreundii (3,250)           | ≤10                 | [cgmlst.org complex type distance](https://www.cgmlst.org/ncs/schema/Cfreundii/)           | [Kieninger et al. 2025](https://doi.org/10.1128/jcm.00860-25)                    |
| [_Enterobacter hormaechei_](ehormaechei.md)               | `ehormaechei`  | cgmlst.org Ehormaechei (2,178)         | ≤12                 | [cgmlst.org complex type distance](https://www.cgmlst.org/ncs/schema/Ehormaechei/)         | [Prior et al. 2025](https://doi.org/10.1128/jcm.00369-25)                        |
| [_Enterobacter cloacae_ complex](ecloacae.md)             | `ecloacae`     | Chewie-NS ECC cgMLST (1,812)           | ≤3 (borderline ≤5)  | [Miller et al. 2026](https://doi.org/10.64898/2026.09.14.751580) (preprint)                | [Miller et al. 2026](https://doi.org/10.64898/2026.09.14.751580)                 |
| [_Stenotrophomonas maltophilia_ complex](smaltophilia.md) | `smaltophilia` | Gröschel 2020 wgMLST (17,603)          | ≤10                 | [Gröschel et al. 2020](https://doi.org/10.1038/s41467-020-15123-0) (d10)                   | [Gröschel et al. 2020](https://doi.org/10.1038/s41467-020-15123-0)               |

Only the _K. oxytoca_, _E. cloacae_ complex and _S. maltophilia_ thresholds come
from a paper that tested them on isolates; the cgmlst.org values are the complex type distances
the scheme authors publish with each scheme. Treat them all as guides: see
[caveats](../results/caveats.md).

## From laboratory label to schema

The `growth` column of the metadata is mapped to a schema by
[`assets/species_map.tsv`](https://github.com/ryanjameskennedy/sinklink/blob/master/assets/species_map.tsv):

| `growth`                                               | Schema         |
| ------------------------------------------------------ | -------------- |
| `pseudomonas_aeruginosa`                               | `paeruginosa`  |
| `klebsiella_pneumoniae`                                | `kpneumoniae`  |
| `klebsiella_oxytoca`, `klebsiella_oxytoca_group`       | `koxytoca`     |
| `serratia_marcescens`                                  | `smarcescens`  |
| `citrobacter_freundii`                                 | `cfreundii`    |
| `enterobacter_cloacae`, `enterobacter_cloacae_complex` | `ecloacae`     |
| `enterobacter_hormaechei`                              | `ehormaechei`  |
| `stenotrophomonas_maltophilia`                         | `smaltophilia` |

The match is exact. An isolate whose label is not in the table is assembled and
QC'd but not allele called.

## Species checks

The laboratory label is not trusted on its own: Kraken2/Bracken must assign at
least 80% of the reads to species the schema covers (`species_pattern`), and no
other genus may exceed 5% (see [quality control](../pipeline/qc.md)). Each
species page lists what its schema accepts.

## Adding a species

1. Add the schema to the `SCHEMAS` list in the `Makefile` with its download
   URL, archive name and seed genome (or `READY_<schema> := yes` for a
   ready-to-use schema from Chewie-NS), and run `make <schema>_all`.
2. Add a row to `assets/schemas.tsv` with the threshold, the accepted species,
   genera and genome size range, the mlst scheme (`mlst --list`) and the source.
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
ecloacae
smaltophilia
```
