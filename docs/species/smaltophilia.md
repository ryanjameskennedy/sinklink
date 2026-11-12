# _Stenotrophomonas maltophilia_ complex

|                  |                                                                                                                                            |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Schema           | `smaltophilia`                                                                                                                             |
| Scheme           | Gröschel et al. 2020 wgMLST ([figshare 10005047](https://figshare.com/articles/dataset/Smaltophilia_wgMLST_all-alleles_fasta_gz/10005047)) |
| Loci             | 17,603 (about 4,174 per genome)                                                                                                            |
| Seed genome      | NC_010943.1 (K279a, used to train Prodigal)                                                                                                |
| Reference genome | [GCF_020641395.2](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_020641395.2/) (ACYCa.6E) (used for QUAST, Mash and variant calling)     |
| Threshold        | ≤10 alleles (d10)                                                                                                                          |
| Lab labels       | `stenotrophomonas_maltophilia`                                                                                                             |

## The scheme

No cgmlst.org scheme exists for _S. maltophilia_, so the wgMLST scheme from
Gröschel et al. (2020) is used. It was built by Applied Maths (bioMérieux) from
171 public genomes: overlapping loci, loci with frequent invalid calls, tandem
repeats and multi-copy loci were removed, leaving 17,603 loci (including the
seven classic MLST loci). On average 4,174 loci (range 3,024–4,536) were found
per genome. The allele sequences are published as a single FASTA, which
`bin/split_alleles.py` splits into one file per locus for chewBBACA.

## Threshold

How the paper defined relatedness:

- Distances were counted over **1,275 core loci** (present in 99% of 1,305
  genomes), not all 17,603.
- **d10** (≤10 mismatched alleles, single-linkage) defined closely related
  strains; **d100** (≤100) defined clonal complexes, which often spanned
  different countries and are too loose to indicate transmission.
- Thresholds were chosen from the distribution of pairwise differences, not
  validated against known outbreaks.
- 270 strains fell into 62 d10 clusters; 13 clusters held isolates from the same
  hospital in the same year, and three were respiratory isolates from different
  patients in one hospital within ≤8 weeks. The authors call these potential
  transmission clusters needing epidemiological confirmation.
- Lineages made up mainly of environmental strains (Sgn1–4, Sm1, Sm15) never
  formed d10 clusters and were under-sampled, so the threshold is least tested
  for sink isolates.
- Alleles were called in BioNumerics by combining assembly-free (k-mer) and
  assembly-based (BLAST) calls. chewBBACA calls alleles differently, so counts
  will not match the paper exactly: treat 10 as a guide.

sinklink counts differences over all wgMLST loci called in both isolates (the
paper's list of 1,275 core loci is in its supplementary data), and applies no
minimum fraction of called loci, since each genome carries only about a quarter
of the scheme.

## Species check

The schema accepts any _Stenotrophomonas_ species, since the complex spans 23
lineages.

| Setting in `assets/schemas.tsv` | Value               |
| ------------------------------- | ------------------- |
| `species_pattern`               | `^Stenotrophomonas` |
| `genera`                        | Stenotrophomonas    |
| Expected genome size            | 4.1–5.4 Mb          |
| `mlst_scheme`                   | `smaltophilia`      |

## In the VASK study

Transmission_2 (5 days, same patient, sink positive before the airway sample):
the best fit for sink-to-patient spread. Over 5 days a genuine link should be
close to 0 differences; a count near 10 is borderline and worth checking with
SNPs (e.g. SKA2).

## Notes

- The _S. maltophilia_ complex is diverse (Gröschel et al. 2020 describe 23 lineages), so many isolates sit far from any single reference and less of their genome is compared in the SNP distances; check `reference_distance` in the QC summary.
- The FASTA header format is assumed to be `<locus>_<allele>`;
  `split_alleles.py` stops if it does not find about 17,603 loci, and
  `--pattern` can be set to match another format.
- figshare may block automated downloads; see [schemas](../setup/schemas.md).

Full citations are in the [references](../reference/references.md).
