# sinklink: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### `Added`

- Type strains for the _Klebsiella pneumoniae_ species complex (8 genomes, `kpneumoniae`) and the _Klebsiella oxytoca_ species complex (6 genomes, `koxytoca`)

### `Changed`

- For schemas with type strains, `species_mismatch` comes from the closest type strain instead of Bracken: an isolate fails unless its ANI to the type strain of a species in the schema's `species_pattern` is 95% or more; schemas without type strains keep the Bracken check
- The `smarcescens` `species_pattern` covers the _S. marcescens_ complex species with a type strain (_S. ureilytica_, _S. sarumanii_, _S. bockelmannii_, _S. nevei_ and _S. montpellierensis_ added)
- `many_contigs`, `low_n50` and `genome_size` fail instead of warn, and `contamination` warns instead of failing

## v0.5.0 - 2026-11-18

Adds ANI, read and allele QC, a species call from type strains, an
_E. cloacae_ complex schema and a download of the full Kraken2 database, and
keeps SNP distances from stopping a run when Gubbins cannot run. The ANI, read
QC and `ecloacae` steps have run on real data on thedonkey; the Gubbins
changes and the species call have only run as stubs and on test inputs.

### `Added`

- A species call within schemas that cover several close species: skani ANI from each assembly to the type strains in `assets/type_strains.tsv` (`ani/<sample>.type_strains.tsv`), with the closest type strain, its ANI and the species at 95% or more in `qc_summary.tsv` and the report, the species in the isolate hover labels and each group's summary line, pairs of different species flagged in `pairwise_distances.tsv` (`species_a`, `species_b` and a note) and their hover labels, and a species figure per transmission group: a heatmap of skani ANI between every two of its isolates and type strains (`ani/groups/<group>.tsv`, nf-core `skani/triangle`) with a tree clustered on the same ANI; `make type_strains` downloads them (part of `make install`), for the _Serratia marcescens_ complex (8 genomes) and the _Enterobacter cloacae_ complex and its close relatives (34 genomes, for `ecloacae` and `ehormaechei`)
- An _Enterobacter cloacae_ complex schema (`ecloacae`): the Miller et al. 2026 cgMLST from Chewie-NS (1,812 loci), threshold ≤3 alleles, borderline ≤5, with GCF_905331265.2 as reference; `make ecloacae_all` unpacks the ready-to-use schema without PrepExternalSchema
- `make kraken_db` downloads the full Kraken2 Standard database (85 GB), or another one with `KRAKEN_DB` and `KRAKEN_DB_DATE`
- skani ANI from each assembly to its schema's reference genome (`ani/`), checked against 95% (`distant_reference`); the Mash distance is only checked when there is no ANI
- Reads, the share mapped back to the own assembly (`samtools flagstat`, warns below 90% as `low_mapped_reads`) and breadth in `qc_summary.tsv`
- Missing loci and novel alleles per isolate in `allele_qc.tsv`
- A table of every isolate's reads, depth, ANI, missing loci and novel alleles in the transmission report
- The report's table of every isolate gives the assembly size and the reference genome's size, which `qc_summary.tsv` now has as `reference_length` (from QUAST)
- The report lists the paths of the databases the run used, and the figures and thresholds table give each schema's number of loci
- Hover labels on every point in the report's figures (pair, distances, days and sample types; isolate, sample type and date; QC values and flags), also in the SVG files; the report now embeds the figures as inline SVG

### `Changed`

- Gubbins is skipped unless 4 or more sequences in a schema's alignment are at most 25% `N` or gap (its own cut-off, and the 4 RAxML needs for a tree), and a schema whose Gubbins run fails gets SNP distances without recombination removed, instead of stopping the run; the share missing per sequence is in `snp_distances/<schema>.missing.tsv`
- `enterobacter_cloacae` and `enterobacter_cloacae_complex` isolates are typed with `ecloacae` instead of `ehormaechei`; `enterobacter_hormaechei` maps to `ehormaechei`
- The isolate QC figure labels depth as over the isolate's own assembly, colours isolates by QC status, marks Nanopore isolates with triangles, keeps nearby points apart, zooms the percentage axes to the data and moves the cut-off labels into the legend
- mlst types each isolate with its schema's scheme (`mlst_scheme` in `assets/schemas.tsv`, passed as `--scheme`) instead of detecting it; `ecloacae` and `ehormaechei` use the PubMLST _E. cloacae_ scheme, which covers the complex
- The docs no longer hold settings for our own servers, which live in [ryanjameskennedy/configs](https://github.com/ryanjameskennedy/configs); the server docs give general recommendations instead, including how much memory to reserve for Kraken2 with the full Standard database

## v0.4.0 - 2026-11-11

Adds a transmission report with publication figures and redraws the metro map.
The report has run on the first VASK data on thedonkey; the SNP steps have
still only run as stubs.

### `Added`

- Transmission report (`report/transmission_report.html`) and publication figures (`report/figures/`) drawn with matplotlib: distances per group, distance against time, allele against SNP distance, sampling timelines, minimum spanning trees, isolates by QC status and isolate QC, plus `report/table1.tsv` with one line per transmission group
- `--skip_report`, `--report_formats` and `--report_environment_types`

### `Changed`

- The metro map is redrawn: one track per stage with the Illumina / Nanopore tools named together, read QC on top and the SNP track at the bottom, the assembly splitting into an assembly QC track (shaded yellow) and a typing track (shaded green), and the distances feeding the transmission report; `docs/render_metro_map.py` draws it

## v0.3.0 - 2026-11-11

Rebuilds the SNP distances from existing tools, masking repeats, prophages,
low-depth regions and recombination, and fixes the setup and server settings
found on the first run on thedonkey. The SNP steps are tested with stub runs
only; they have not yet run on real reads.

### `Added`

- SNP distances from masked pseudogenomes built with existing tools: repeats from a MUMmer self-alignment and prophages from PhiSpy are masked with the low-depth regions (mosdepth) when `bcftools consensus` applies each isolate's SNPs; Gubbins removes recombination for schemas with 3 or more sequences and snp-dists counts the differences
- `make references` also downloads each reference's GenBank file for PhiSpy
- `snp_recombination_filtered` in the pair table
- Links from the species threshold table to each threshold's source, and DOIs for the Kampmeier, Kieninger and Prior papers

### `Changed`

- The setup Makefiles run their containers with `singularity` (`SINGULARITY=apptainer` switches runtime)
- The setup examples keep the databases directly under `/mnt/cache/dbs`
- The run examples use `-profile singularity`, as thedonkey's config now sets up Singularity and mounts `/media/shortterm`, where `TMPDIR` points

### `Fixed`

- A `0` allele call counts as missing, as in cgmlst-dists, so two missing calls never count as a match
- PhiSpy finds its GenBank output when the input file name has dots, such as an NCBI accession (nf-core module patch)
- `make references` keeps the reference FASTA files; make treated them as temporary and deleted them after indexing
- Setup log messages with brackets no longer break the shell command
- The species check tables on the _K. oxytoca_, _K. pneumoniae_ and _S. marcescens_ pages, which the `|` in their species patterns split into extra columns

### `Removed`

- The home-made pseudogenome script (`make_pseudogenome.py`) and the samtools depth step, replaced by the tools above
- `snp_sites_compared` in the pair table

## v0.2.0 - 2026-11-08

Adds human read removal, variant calling against a reference genome per species
and SNP distances next to the allele distances, and moves server settings out of
the pipeline. Tested with stub runs only; not yet validated on real data.

### `Added`

- Documentation on running on a server, with each tool's label and its nf-core, JASEN and thedonkey resources
- nf-core template features: nf-test tests with snapshots, the template CI (linting, nf-test, branch protection), RO-Crate metadata, nf-core/configs profiles, and email, Slack and Teams notifications
- `lims_id` metadata column, shown in the allele QC and pair tables
- Metro map of the pipeline (`assets/metro_map.mmd`, drawn with nf-metro) in the README and docs
- Human read removal with Deacon and the `panhuman-1` index before every other step (`--deacon_index`, `--skip_host_removal`, `--save_host_removed_reads`; `make deacon_index`)
- A reference genome per schema (NCBI RefSeq reference, `reference` column of `assets/schemas.tsv`), downloaded with jasentool as FASTA and GFF by `make references` (`--references_dir`)
- QUAST compares each assembly with its reference genome, and the QC summary reports the genome fraction and the Mash distance to the reference, with a `distant_reference` warning above 0.05
- Variant calling against the reference genome: Snippy for Illumina, minimap2 and Clair3 (bacterial model, `--clair3_model`) for Nanopore, published as VCFs (`--skip_variant_calling`)
- A masked pseudogenome per isolate and pairwise SNP distances within each transmission group, reported next to the allele differences (`--snp_min_depth`)
- `test_full` profile (the test inputs with every optional step on), which `nf-core pipelines download` needs to list the containers
- A test with host removal, variant calling and allele calling skipped
- Docs on how to download the Standard-16 Kraken2 database, and on what the species thresholds mean for calling the same colonisation
- `containers/Makefile` also downloads jasentool and samtools for `make references`

### `Changed`

- SKESA and chewBBACA use their nf-core label resources instead of custom ones
- Labels follow the JASEN resources: SKESA, chewBBACA and Snippy `process_high`, NanoPlot, gambitcore and minimap2 `process_medium` (nf-core module patches)
- Removed the `thedonkey` profile: pass the server config with `-c` and the database paths with `-params-file` (see ryanjameskennedy/configs)
- Metadata columns: `translation_id` is now `sample` and `sample` (the sample type) is now `sample_type`; the QC tables use `sample` too
- The stub CI workflow `ci.yml` is replaced by nf-test
- The test samplesheet points at the test reads on GitHub, so tests run from any folder
- `--kraken_db` is required and the Kraken2/Bracken species check always runs
- The distance check also runs with `--skip_chewbbaca`, reporting SNP distances only
- Metadata dates are read as ISO 8601 date-times (`YYYY-MM-DDTHH:MM:SS`, or `YYYY-MM-DD`)
- The setup's chewBBACA and samtools images are the ones the pipeline uses, saved under the names Nextflow caches them as, so the pipeline reuses them when `CONTAINERS_DIR` is its Apptainer cache
- The nf-test and pipeline download CI jobs run on Ubuntu 24.04, and the download job tests the pull request's own branch
- Pull requests into `master` may also come from `release/*` branches

### `Fixed`

- The chewBBACA version is read from its version line only; the Python warning chewBBACA 3.5.4 prints made the software versions file invalid
- Clair3 finds its bundled models under Apptainer (nf-core module patch)
- The local modules use their Singularity images under Apptainer, as the nf-core modules do

### `Removed`

- SPAdes and the `--assembler` parameter: Illumina reads are always assembled with SKESA
- The nf-core template version comment workflow, which needs the nf-core bot's token

## v0.1.0 - 2026-11-06

First release of sinklink, created with the [nf-core](https://nf-co.re/) template.
Tested with stub runs only; not yet validated on real data.

### `Added`

- Read preparation: optional Trimmomatic (Illumina) and Filtlong (Nanopore), FastQC and NanoPlot
- Assembly: SKESA or SPAdes for Illumina, Flye and Medaka for Nanopore
- Assembly QC: QUAST, gambitcore, read depth over the own assembly, 7-gene MLST
- Species check with Kraken2 and Bracken against the species each schema covers
- chewBBACA AlleleCall per schema and pairwise distances within transmission groups, flagged by QC
- Makefile for schema setup (seed genome, Prodigal training, download, PrepExternalSchema) and the GAMBIT database
- `thedonkey` profile and a stub `test` profile
- Documentation on Read the Docs, with one page per species and the source of each threshold
- GitHub Actions: stub runs on Nextflow 25.04.0 and a strict docs build

### `Fixed`

### `Dependencies`

### `Deprecated`
