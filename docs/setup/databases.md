# Databases

| Database           | Set up with         | Parameter          | Needed                                           |
| ------------------ | ------------------- | ------------------ | ------------------------------------------------ |
| Kraken2/Bracken    | `make kraken_db`    | `--kraken_db`      | always                                           |
| Deacon human index | `make deacon_index` | `--deacon_index`   | unless `--skip_host_removal`                     |
| Reference genomes  | `make references`   | `--references_dir` | unless `--skip_variant_calling`                  |
| Type strains       | `make type_strains` | `--references_dir` | optional; species are not named without them     |
| GAMBIT             | `make gambit_db`    | `--gambit_db`      | optional; completeness is not checked without it |

## Reference genomes

Each schema has one reference genome, its accession in the `reference` column
of `assets/schemas.tsv`: NCBI's RefSeq reference genome for the species, a
complete and annotated assembly. `make references` downloads each one from
NCBI Datasets with `jasentool download-ncbi`, as JASEN does, into
`<ASSETS_DIR>/references` as `<accession>.fasta` and `<accession>.gff`, then
indexes it with `samtools faidx`. It also downloads the GenBank file
(`<accession>.gbff`), which PhiSpy needs to find prophages. Pass the folder with `--references_dir`.

| Schema       | Reference genome | Strain        |
| ------------ | ---------------- | ------------- |
| paeruginosa  | GCF_000006765.1  | PAO1          |
| kpneumoniae  | GCF_000240185.1  | HS11286       |
| koxytoca     | GCF_900636985.1  | NCTC13727     |
| smarcescens  | GCF_030291735.1  | ELP1.10       |
| cfreundii    | GCF_904859905.1  | MSB1_1H       |
| ehormaechei  | GCF_019048245.1  | FDAARGOS 1433 |
| ecloacae     | GCF_905331265.2  | 1382          |
| smaltophilia | GCF_020641395.2  | ACYCa.6E      |

To use another reference, change the accession in your copy of the schema
table (`--schema_table`) and run `make references` again.

QUAST and Mash use the references whenever `--references_dir` is set, also
with `--skip_variant_calling`.

## Type strains

Some schemas cover several closely related species that Kraken2 and the
laboratory often cannot tell apart, and whose genomes sit just around the 95%
ANI species boundary from each other. For these, `assets/type_strains.tsv`
lists the genome of the type strain of each species, and each isolate's
assembly is compared with them with skani to name its species (see
[QC](../pipeline/qc.md#species-call)). `make type_strains` downloads them like
the reference genomes, into the same folder (`--references_dir`); it is part of
`make install`.

| Schema      | Species                                  | Strain     | Genome          |
| ----------- | ---------------------------------------- | ---------- | --------------- |
| smarcescens | _Serratia marcescens_                    | ATCC 13880 | GCF_017654245.1 |
| smarcescens | _Serratia marcescens_ subsp. _sakuensis_ | KCTC 42172 | GCF_003428265.1 |
| smarcescens | _Serratia ureilytica_                    | JCM 16474  | GCF_039523675.1 |
| smarcescens | _Serratia sarumanii_                     | K-M0706    | GCF_029962605.1 |
| smarcescens | _Serratia bockelmannii_                  | S3         | GCF_008011855.1 |
| smarcescens | _Serratia nevei_                         | LMG 31536  | GCF_037948395.1 |
| smarcescens | _Serratia nematodiphila_                 | DSM 21420  | GCF_000738675.1 |

KCTC 42172 is not marked as type material in NCBI, and _S. marcescens_ subsp.
_sakuensis_ is now a synonym of _S. marcescens_, so it is a second
_S. marcescens_ genome.

For `ecloacae` and `ehormaechei`, the table lists the type strains of the 34
_Enterobacter_ species and subspecies with a type-strain genome in NCBI RefSeq,
the _E. cloacae_ complex and its close relatives: among them _E. hormaechei_
(DSM 12409, and the type strains of its subspecies _hoffmannii_, _oharae_,
_steigerwaltii_ and _xiangfangensis_), _E. asburiae_ (ATCC 35953),
_E. cloacae_ (ATCC 13047), _E. kobei_ (DSM 13645), _E. ludwigii_ (EN-119),
_E. roggenkampii_ (DSM 16690) and _E. bugandensis_ (EB-247). An isolate is
compared with the panel of its own schema; one row can name several schemas,
separated by commas.

To add a species, add its schema, species, strain and genome accession to your
copy of the table (`--type_strains`) and run `make type_strains` again.

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

`make kraken_db` downloads the full Standard database (RefSeq archaea,
bacteria, viral, plasmid, human and UniVec_Core, 2026-06-26 release) from the
[Langmead lab index](https://benlangmead.github.io/aws-indexes/k2) into
`<ASSETS_DIR>/kraken2/standard_20260626` and unpacks it. The archive is 85 GB,
so check the disk first:

```bash
make kraken_db ASSETS_DIR=/path/to/dbs
```

Pick another database or release with `KRAKEN_DB` and `KRAKEN_DB_DATE`, using
the names on the index page, e.g. `make kraken_db KRAKEN_DB=pluspf` (adds
protozoa and fungi) or `KRAKEN_DB=standard_16_GB`. sinklink runs Kraken2 with
`--memory-mapping`, which reads the database from disk instead of loading it
into memory, so the full database also runs on a server with less memory than
the database; it is slower than a database that fits in memory, mostly on the
first sample. See [running on a server](servers.md) for how much memory to
reserve for it.

Standard-16 is the same database capped at 16 GB. The cap drops some k-mers,
which costs a little sensitivity, most for close relatives within a genus such
as the members of the _E. cloacae_ complex; a cultured isolate has plenty of
reads from one species, so this matters less than for metagenomes. The Standard-16
archive is 12 GB:

```bash
make kraken_db KRAKEN_DB=standard_16_GB ASSETS_DIR=/path/to/dbs
```

Unpacked, either folder holds the Kraken2 files
(`hash.k2d`, `opts.k2d`, `taxo.k2d`) and the Bracken k-mer distributions
(`database<length>mers.kmer_distrib`) for a range of read lengths. Pass the
folder with `--kraken_db`. For a newer release, take the file name from the
index page.

Bracken needs the `database<length>mers.kmer_distrib` file for the read length
given with `--bracken_read_length` (default 150); if Bracken fails, the Kraken2
report is used instead.

On a server, set them in the parameters file (see [running on a server](servers.md)).
