# Pipeline steps

```text
reads ──► READ_PREPARATION ──► ASSEMBLY ──► ASSEMBLY_QC ──┐
   │      (filter, read QC)    (per platform) (QUAST, depth,│
   │                                           MLST, ...)   ├──► SUMMARISE_QC ──► qc_summary.tsv ──┐
   └────► SPECIES_CHECK (Kraken2/Bracken) ─────────────────┘                                      │
                               ASSEMBLY ──► ALLELE_CALLING (chewBBACA per schema) ──► CHECK_DISTANCES ◄┘
                                                                                      (pairs per group)
```

The workflow
([`workflows/sinklink.nf`](https://github.com/ryanjameskennedy/sinklink/blob/master/workflows/sinklink.nf))
runs five local subworkflows built from nf-core modules:

| Subworkflow        | Illumina                                                                     | Nanopore                                                                                                 |
| ------------------ | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `READ_PREPARATION` | Trimmomatic (with `--trim`), FastQC                                          | Filtlong (with `--filtlong`), NanoPlot                                                                   |
| `ASSEMBLY`         | SKESA, or SPAdes `--isolate`                                                 | Flye `--nano-hq` (`--asm-coverage 50` with the schema's genome size), then `medaka_consensus --bacteria` |
| `ASSEMBLY_QC`      | QUAST, gambitcore, `bwa mem` to the own assembly + `samtools coverage`, mlst | QUAST, gambitcore, `minimap2 -x lr:hq` to the own assembly + `samtools coverage`, mlst                   |
| `SPECIES_CHECK`    | Kraken2 (`--memory-mapping`) and Bracken (species level)                     | same                                                                                                     |
| `ALLELE_CALLING`   | chewBBACA AlleleCall per schema, `--no-inferred`                             | same                                                                                                     |

Then two local modules finish the run:

- `SUMMARISE_QC` (`bin/summarise_qc.py`) writes one QC row per isolate, and the
  rows are combined into `qc_summary.tsv`. See [quality control](qc.md).
- `CHECK_DISTANCES` (`bin/check_distances.py`) compares isolates within each
  transmission group. See [interpreting the results](../results/interpreting.md).

MultiQC collects FastQC, NanoPlot, QUAST and Kraken2 results into one report.

## Design choices

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
