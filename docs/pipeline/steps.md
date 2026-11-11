# Pipeline steps

```text
reads ──► READ_PREPARATION ──► ASSEMBLY ──► ASSEMBLY_QC ──┐
          (human read removal,  (per platform) (QUAST, ANI,  │
           filter, read QC)                   depth, MLST)  ├──► SUMMARISE_QC ──► qc_summary.tsv ──┐
             ├──► SPECIES_CHECK (Kraken2/Bracken) ──────────┘                                      │
             └──► VARIANT_CALLING (Snippy or Clair3, masked pseudogenomes, Gubbins, snp-dists) ───┤
                               ASSEMBLY ──► ALLELE_CALLING (chewBBACA per schema) ──► CHECK_DISTANCES ◄┘
                                                                                      (pairs per group)
                                                                                             │
                                                                                     TRANSMISSION_REPORT
                                                                                   (HTML report, figures)
```

The workflow
([`workflows/sinklink.nf`](https://github.com/ryanjameskennedy/sinklink/blob/master/workflows/sinklink.nf))
runs six local subworkflows built from nf-core modules:

| Subworkflow        | Illumina                                                                                                                                                                            | Nanopore                                                                                                                                           |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `READ_PREPARATION` | Deacon human read removal, Trimmomatic (with `--trim`), FastQC                                                                                                                      | Deacon human read removal, Filtlong (with `--filtlong`), NanoPlot                                                                                  |
| `ASSEMBLY`         | SKESA                                                                                                                                                                               | Flye `--nano-hq` (`--asm-coverage 50` with the schema's genome size), then `medaka_consensus --bacteria`                                           |
| `ASSEMBLY_QC`      | QUAST, Mash and skani against the reference genome, gambitcore, `bwa mem` to the own assembly + `samtools coverage` and `flagstat`, mlst                                            | QUAST, Mash and skani against the reference genome, gambitcore, `minimap2 -x lr:hq` to the own assembly + `samtools coverage` and `flagstat`, mlst |
| `SPECIES_CHECK`    | Kraken2 (`--memory-mapping`) and Bracken (species level)                                                                                                                            | same                                                                                                                                               |
| `VARIANT_CALLING`  | Snippy (`bwa mem` and FreeBayes) against the reference genome; then for both platforms, masked pseudogenomes (MUMmer, PhiSpy, mosdepth, bcftools), Gubbins and snp-dists per schema | `minimap2 -x lr:hq` to the reference genome, then Clair3 in haploid mode                                                                           |
| `ALLELE_CALLING`   | chewBBACA AlleleCall per schema, `--no-inferred`                                                                                                                                    | same                                                                                                                                               |

Then local modules finish the run:

- `SUMMARISE_QC` (`bin/summarise_qc.py`) writes one QC row per isolate, and the
  rows are combined into `qc_summary.tsv`. See [quality control](qc.md).
- `CHECK_DISTANCES` (`bin/check_distances.py`) compares isolates within each
  transmission group, by allele differences against the species threshold, with
  the SNP distances from snp-dists alongside. See
  [interpreting the results](../results/interpreting.md).
- `TRANSMISSION_REPORT` (`bin/transmission_report.py`) draws the transmission
  report and the publication figures from those tables with matplotlib. See
  [output](../output.md#transmission-report).

MultiQC collects FastQC, NanoPlot, QUAST and Kraken2 results into one report.

## Design choices

- **Human reads removed first.** Deacon with the `panhuman-1` index runs
  before every other step. It had the highest balanced accuracy for both short
  and long reads in its authors' benchmark
  ([Constantinides et al. 2025](https://doi.org/10.1101/2025.06.09.658732)), and
  was among the most accurate and fastest tools in an independent comparison
  ([Zentgraf et al. 2025](https://doi.org/10.1093/bioinformatics/btaf632)).
  Neither study is neutral (each is by the authors of one of the tools), and
  the independent benchmark that ranked Bowtie2 `--very-sensitive-local`
  against T2T-CHM13 best did not include Deacon
  ([Forbes et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12664888/)).
- **Snippy for Illumina, Clair3 for Nanopore.** Snippy (`bwa mem` and
  FreeBayes) had the best overall rank of 41 bacterial SNP calling pipelines
  and coped best with a distant reference
  ([Bush et al. 2020](https://doi.org/10.1093/gigascience/giaa007)). Clair3 and
  DeepVariant beat every traditional caller on bacterial Nanopore data and
  matched or beat Illumina from 10× depth
  ([Hall et al. 2024](https://doi.org/10.7554/eLife.98300)); Clair3 is lighter
  to run, and its default model here was fine-tuned on bacterial genomes from
  that study. No benchmark has tested deep-learning callers on bacterial
  Illumina reads.
- **One reference per schema.** Each schema's reference genome is NCBI's
  RefSeq reference for the species, so results are comparable across runs.
  For the diverse species complexes it can sit far from some isolates; the
  Mash distance in the QC summary flags those, as Bush et al. recommend.
- **SNP distances for information.** SNP distances within a group are reported
  next to the allele differences but have no threshold: published SNP
  cut-offs for these species are not standardised the way the cgMLST ones
  are, and they depend on the reference and the masking.
- **Masking with existing tools.** Repeats come from a MUMmer self-alignment of
  the reference, as in PhaME; prophages from PhiSpy, which is built for
  complete bacterial genomes; recombination from Gubbins, as in nf-core/bactmap.
  The masks are applied after mapping: masking the reference first makes reads
  map to the wrong place.

- **`--no-inferred`.** AlleleCall never adds alleles to the schemas, so
  parallel jobs are safe and repeat runs reproducible; novel alleles are still
  numbered consistently within a run.
- **Depth over the own assembly.** Reads are mapped back to each isolate's own
  assembly rather than to a reference, so depth is measured even when the
  species is not what the lab reported.
- **One Medaka round.** JASEN polishes Flye assemblies twice; sinklink uses one
  round, as the nf-core module does and Medaka's documentation recommends.
- **Bracken fallback.** If Bracken fails, the Kraken2 report is used for the
  species check.
