# Parameters

The full schema, with types and validation, is
[`nextflow_schema.json`](https://github.com/ryanjameskennedy/sinklink/blob/master/nextflow_schema.json);
`nextflow run ryanjameskennedy/sinklink --help` prints it.

## Input and output

| Parameter    | Meaning                                                  | Default  |
| ------------ | -------------------------------------------------------- | -------- |
| `--input`    | Samplesheet (`sample,platform,fastq_1,fastq_2`)          | required |
| `--metadata` | Study metadata (`sample`, `transmission`, `growth`, ...) | required |
| `--outdir`   | Output folder                                            | required |

## Schemas and databases

| Parameter         | Meaning                                                         | Default                            |
| ----------------- | --------------------------------------------------------------- | ---------------------------------- |
| `--schemas_dir`   | Folder with `<schema>/alleles_rereffed`                         | required unless `--skip_chewbbaca` |
| `--kraken_db`     | Kraken2/Bracken database; species check skipped without it      | none                               |
| `--gambit_db`     | GAMBIT database for gambitcore; completeness skipped without it | none                               |
| `--schema_table`  | Thresholds, accepted species and genome size per schema         | `assets/schemas.tsv`               |
| `--species_map`   | Laboratory growth label to schema                               | `assets/species_map.tsv`           |
| `--qc_thresholds` | Read and assembly QC thresholds per platform                    | `assets/qc_thresholds.tsv`         |

## Analysis

| Parameter               | Meaning                                | Default                                             |
| ----------------------- | -------------------------------------- | --------------------------------------------------- |
| `--assembler`           | `skesa` or `spades` for Illumina reads | `skesa`                                             |
| `--trim`                | Trim Illumina reads with Trimmomatic   | off                                                 |
| `--trimmomatic_args`    | Trimmomatic steps                      | `LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36` |
| `--filtlong`            | Filter Nanopore reads with Filtlong    | off                                                 |
| `--filtlong_args`       | Filtlong options                       | `--min_length 1000 --min_mean_q 90`                 |
| `--bracken_read_length` | Bracken k-mer distribution read length | 150                                                 |
| `--skip_chewbbaca`      | Stop after assembly and QC             | off                                                 |

The trimming and filtering defaults are JASEN's.
