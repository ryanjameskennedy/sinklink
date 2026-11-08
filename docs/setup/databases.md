# Databases

| Database           | Set up with                                    | Parameter          | Needed                                           |
| ------------------ | ---------------------------------------------- | ------------------ | ------------------------------------------------ |
| Kraken2/Bracken    | [download once](#kraken2bracken-species-check) | `--kraken_db`      | always                                           |
| Deacon human index | `make deacon_index`                            | `--deacon_index`   | unless `--skip_host_removal`                     |
| Reference genomes  | `make references`                              | `--references_dir` | unless `--skip_variant_calling`                  |
| GAMBIT             | `make gambit_db`                               | `--gambit_db`      | optional; completeness is not checked without it |

## Reference genomes

Each schema has one reference genome, its accession in the `reference` column
of `assets/schemas.tsv`: NCBI's RefSeq reference genome for the species, a
complete and annotated assembly. `make references` downloads each one from
NCBI Datasets with `jasentool download-ncbi`, as JASEN does, into
`<ASSETS_DIR>/references` as `<accession>.fasta` and `<accession>.gff`, then
indexes it with `samtools faidx`. Pass the folder with `--references_dir`.

| Schema       | Reference genome | Strain        |
| ------------ | ---------------- | ------------- |
| paeruginosa  | GCF_000006765.1  | PAO1          |
| kpneumoniae  | GCF_000240185.1  | HS11286       |
| koxytoca     | GCF_900636985.1  | NCTC13727     |
| smarcescens  | GCF_030291735.1  | ELP1.10       |
| cfreundii    | GCF_904859905.1  | MSB1_1H       |
| ehormaechei  | GCF_019048245.1  | FDAARGOS 1433 |
| smaltophilia | GCF_020641395.2  | ACYCa.6E      |

To use another reference, change the accession in your copy of the schema
table (`--schema_table`) and run `make references` again.

QUAST and Mash use the references whenever `--references_dir` is set, also
with `--skip_variant_calling`.

## Deacon (human read removal)

`make deacon_index` downloads the `panhuman-1` index (k=31, w=15, 3.3 GB) into
`<ASSETS_DIR>/deacon`. It is built from the Human Pangenome Reference
Consortium year 1 assemblies, CHM13 and GRCh38, minus sequences shared with
bacterial and viral genomes. Pass the file with `--deacon_index`. Deacon needs
about 5 GB of memory with it.

## GAMBIT (completeness)

gambitcore estimates assembly completeness against the core k-mers of the
closest species in the GAMBIT RefSeq curated 1.0 database. `make gambit_db`
downloads it into `<ASSETS_DIR>/gambit_db`, as JASEN does. Pass the folder with
`--gambit_db`.

## Kraken2/Bracken (species check)

`make install` does not download a Kraken2 database: they are large, and a
server often has one already. Point the pipeline at it with `--kraken_db`,
which is required.

To download one, use a prebuilt database from the
[Langmead lab index](https://benlangmead.github.io/aws-indexes/k2). sinklink
uses Standard-16, the RefSeq archaea, bacteria, viral, plasmid, human and
UniVec_Core database capped at 16 GB, so it fits in memory on any of our
servers. The cap drops some k-mers, which costs a little sensitivity; a
cultured isolate has plenty of reads from one species, so this matters less
than for metagenomes. The 2026-06-26 release used on thedonkey:

```bash
mkdir -p /mnt/cache/dbs/kraken2/standard_16gb_20260626
cd /mnt/cache/dbs/kraken2/standard_16gb_20260626
wget https://genome-idx.s3.amazonaws.com/kraken/k2_standard_16_GB_20260626.tar.gz
tar -xzf k2_standard_16_GB_20260626.tar.gz
rm k2_standard_16_GB_20260626.tar.gz
```

The archive is 12 GB. Unpacked, the folder holds the Kraken2 files
(`hash.k2d`, `opts.k2d`, `taxo.k2d`) and the Bracken k-mer distributions
(`database<length>mers.kmer_distrib`) for a range of read lengths. Pass the
folder with `--kraken_db`. For a newer release, take the file name from the
index page.

Bracken needs the `database<length>mers.kmer_distrib` file for the read length
given with `--bracken_read_length` (default 150); if Bracken fails, the Kraken2
report is used instead.

On a server, set them in the parameters file (see [running on a server](servers.md)).
