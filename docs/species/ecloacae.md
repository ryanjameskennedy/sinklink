# _Enterobacter cloacae_ complex

|                  |                                                                                                                                                              |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Schema           | `ecloacae`                                                                                                                                                   |
| Scheme           | Chewie-NS [_Enterobacter cloacae_ complex cgMLST](https://chewbbaca.online/species/21) (species 21, schema 1)                                                |
| Loci             | 1,812                                                                                                                                                        |
| Prodigal         | the training file that comes with the schema, from _E. cloacae_ isolate 1382                                                                                 |
| Reference genome | [GCF_905331265.2](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_905331265.2/) (_E. cloacae_ isolate 1382) (used for QUAST, Mash, ANI and variant calling) |
| Threshold        | ≤3 alleles, borderline ≤5                                                                                                                                    |
| Lab labels       | `enterobacter_cloacae`, `enterobacter_cloacae_complex`                                                                                                       |

## Scheme

Miller et al. (2026) built the scheme with chewBBACA from 372 complete and 3,070
draft genomes covering 27 species and subspecies of the complex, each checked
against the type strains with FastANI. Its 1,812 loci are present in at least
99% of those genomes, so it can type _E. cloacae_, _E. hormaechei_,
_E. kobei_, _E. asburiae_ and the rest of the complex with one scheme. It is a
ready-to-use chewBBACA schema: `make ecloacae_all` downloads and unpacks it
(136 MB), without PrepExternalSchema.

EnteroBase has no _Enterobacter_ database or scheme, and cgmlst.org only has
one for _E. hormaechei_ (`ehormaechei`).

## Threshold

In the two outbreaks Miller et al. tested, an _E. cloacae_ outbreak in New
Zealand and four _E. hormaechei_ clusters in a German neonatal unit, linked
isolates were 0–3 alleles apart, and unlinked isolates at least 669. The
authors suggest 3 alleles for recent transmission, and 5 for more sensitivity,
for example over longer outbreaks. Pairs with 4–5 differences are reported as
`borderline`.

```{note}
The paper is a preprint, and its threshold rests on two small outbreaks (25
and 27 isolates). Sink colonisation spans months to years, so `borderline`
pairs deserve a look with SNPs and the dates.
```

## Species check

The schema accepts any _Enterobacter_ species.

| Setting in `assets/schemas.tsv` | Value             |
| ------------------------------- | ----------------- |
| `species_pattern`               | `^Enterobacter\b` |
| `genera`                        | Enterobacter      |
| Expected genome size            | 4.3–5.8 Mb        |

## In the VASK study

Transmission_1 (59 days).

## Notes

- The reference is _E. cloacae_. The other members of the complex are separate
  species, below 95% ANI from it, so _E. hormaechei_ and other non-_cloacae_
  isolates get a `distant_reference` warning and cover less of the reference in the SNP
  distances. The allele distances are not affected.
- Isolates labelled `enterobacter_hormaechei` use the cgmlst.org
  [_E. hormaechei_ scheme](ehormaechei.md) instead.

Full citations are in the [references](../reference/references.md).
