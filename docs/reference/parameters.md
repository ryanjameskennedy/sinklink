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

| Parameter          | Meaning                                                                      | Default                                  |
| ------------------ | ---------------------------------------------------------------------------- | ---------------------------------------- |
| `--schemas_dir`    | Folder with `<schema>/alleles_rereffed`                                      | required unless `--skip_chewbbaca`       |
| `--kraken_db`      | Kraken2/Bracken database for the species check                               | required                                 |
| `--deacon_index`   | Deacon human index, e.g. `panhuman-1.k31w15.idx`                             | required unless `--skip_host_removal`    |
| `--references_dir` | Folder with `<accession>.fasta`, `.fasta.fai`, `.gff` and `.gbff` per schema | required unless `--skip_variant_calling` |
| `--gambit_db`      | GAMBIT database for gambitcore; completeness skipped without it              | none                                     |
| `--schema_table`   | Thresholds, accepted species and genome size per schema                      | `assets/schemas.tsv`                     |
| `--species_map`    | Laboratory growth label to schema                                            | `assets/species_map.tsv`                 |
| `--qc_thresholds`  | Read and assembly QC thresholds per platform                                 | `assets/qc_thresholds.tsv`               |

## Analysis

| Parameter                   | Meaning                                                              | Default                                             |
| --------------------------- | -------------------------------------------------------------------- | --------------------------------------------------- |
| `--skip_host_removal`       | Keep human reads                                                     | off                                                 |
| `--save_host_removed_reads` | Publish the reads after human read removal                           | off                                                 |
| `--trim`                    | Trim Illumina reads with Trimmomatic                                 | off                                                 |
| `--trimmomatic_args`        | Trimmomatic steps                                                    | `LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36` |
| `--filtlong`                | Filter Nanopore reads with Filtlong                                  | off                                                 |
| `--filtlong_args`           | Filtlong options                                                     | `--min_length 1000 --min_mean_q 90`                 |
| `--bracken_read_length`     | Bracken k-mer distribution read length                               | 150                                                 |
| `--skip_variant_calling`    | Skip variant calling and SNP distances                               | off                                                 |
| `--clair3_model`            | Clair3 model for Nanopore reads, bundled in its container            | `r1041_e82_400bps_sup_v430_bacteria_finetuned`      |
| `--snp_min_depth`           | Depth below which a position is masked and left out of SNP distances | 10                                                  |
| `--skip_chewbbaca`          | Skip allele calling                                                  | off                                                 |

The trimming and filtering defaults are JASEN's.
