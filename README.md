# sinklink

Tools for testing whether bacteria isolated from a hospital sink (or other
environmental site) and from a patient belong to the same strain, i.e.
whether the patient's infection or colonisation could have come from the sink.

Starting from Illumina or Nanopore reads, sinklink:

1. QCs the reads (FastQC or NanoPlot, optional Trimmomatic or Filtlong);
2. assembles each isolate (SKESA or SPAdes for Illumina, Flye + Medaka for
   Nanopore);
3. QCs the assembly (QUAST, gambitcore completeness, read depth, 7-gene MLST)
   and confirms the species from the reads (Kraken2/Bracken);
4. calls alleles with [chewBBACA](https://github.com/B-UMMI/chewBBACA) against
   species-specific cgMLST/wgMLST schemas;
5. compares every pair of isolates within each suspected transmission group
   against published, species-specific allele-difference thresholds, flagging
   pairs where either isolate failed QC.

Everything runs on a single server with no job scheduler. Tools, versions,
arguments and the layout of the Makefiles follow
[JASEN](https://github.com/genomic-medicine-sweden/JASEN), so JASEN's
containers and databases can be reused.

- [Background](#background)
- [The dataset](#the-dataset)
- [What the literature says](#what-the-literature-says)
- [Thresholds used](#thresholds-used)
- [Stenotrophomonas maltophilia wgMLST](#stenotrophomonas-maltophilia-wgmlst)
- [Installation](#installation)
- [Running](#running)
- [Pipeline steps](#pipeline-steps)
- [Output](#output)
- [Quality control](#quality-control)
- [Interpreting the results](#interpreting-the-results)
- [Caveats](#caveats)
- [Repository layout](#repository-layout)
- [References](#references)

## Background

Hospital sinks and drains are a recognised reservoir for Gram-negative
opportunists. Biofilms in the drain trap can grow up towards the strainer and
be splashed onto hands, equipment and patients. When the same species turns up
in a sink and in a patient, the question is whether they are the same strain
and, if so, which way it moved.

Whole-genome sequencing answers the first part: two isolates that are only a
few allele differences apart across the core genome are the same strain. The
direction of spread and whether the sink was the source have to come from the
epidemiology (dates, rooms, admission screening).

## The dataset

`vask_colonisation_hidden.csv` lists 26 isolates (13 environmental, 13 airway)
in 9 suspected transmission groups. It is not included in this repository
because it contains study patient identifiers; place it in the repository root
(the default samplesheet path) or pass your own with `--samplesheet`. Columns:

| Column | Meaning |
|---|---|
| `translation_id` | Isolate ID; must match `id` in the reads sheet |
| `transmission` | Suspected transmission group |
| `studypatientnumber` | Study patient (for environmental samples, the patient linked to that site) |
| `sample` | `environment` or `airway` |
| `date` | Sampling date |
| `growth` | Species reported by the laboratory |
| `comment` | Free text |

| Group | Species | Isolates | Span | Notes |
|---|---|---|---|---|
| Transmission_1 | *Enterobacter cloacae* (complex) | 2 environment, 1 airway | 59 days | Lab labels differ ("cloacae" vs "cloacae complex"); confirm species from the genome |
| Transmission_2 | *Stenotrophomonas maltophilia* | 1 environment, 1 airway (same patient) | 5 days | Sink positive before airway: the best fit for sink-to-patient spread |
| Transmission_3 | *Pseudomonas aeruginosa* | 1 environment, 2 airway | 338 days | Patient positive ~10 months before the sink; long span means more expected diversity |
| Transmission_4 | *Klebsiella oxytoca* | 2 environment, 1 airway | 357 days | Environmental isolates a year apart |
| Transmission_5 | *Klebsiella oxytoca* (group) | 1 environment, 1 airway (same patient) | 3 days | Lab labels differ ("oxytoca" vs "oxytoca group") |
| Transmission_6 | *Citrobacter freundii* | 1 environment, 2 airway (same patient) | 3 days | Sink and airway sampled on the same day: direction unknown |
| Transmission_7 | *Serratia marcescens* | 1 environment, 3 airway | 50 days | Three patients |
| Transmission_8 | *Pseudomonas aeruginosa* | 2 environment, 1 airway | 60 days | Patient positive before the second sink |
| Transmission_9 | *Klebsiella pneumoniae* | 2 environment, 1 airway | 68 days | Sink and airway sampled on the same day; second sink later |

Several patients appear in more than one group (different species from the
same sites).

## What the literature says

**1. Confirm the species from the genome first.** Several of these organisms
are species complexes that MALDI-TOF cannot reliably separate. *K. oxytoca* is
often confused with *K. michiganensis* and *K. grimontii*
(Dabernig-Heinz et al. 2024); "*S. marcescens*" NICU outbreaks have turned out
to involve *S. sarumanii* and *S. bockelmannii*; the *E. cloacae* complex
contains many species; *S. maltophilia* is a complex of 23 lineages
(Gröschel et al. 2020). Isolates of different species cannot be the same
strain.

**2. Use cgMLST or core-genome SNPs.** cgMLST gives results comparable to SNP
typing and is easier to standardise between labs (Tönnies et al. 2021). SNPs
give finer resolution for borderline pairs. Seven-gene MLST can only exclude a
link: isolates of the same sequence type can still be unrelated.

**3. There is no universal threshold.** Each cut-off belongs to one species,
one scheme and one allele-calling software. Pipelines differ in how they call
alleles, so counts for the same pair can differ between tools. Near-identical
profiles do not by themselves prove transmission; epidemiological information
is always needed (Tönnies et al. 2021). In the Graz *K. oxytoca* sink outbreak,
an unrelated isolate from the same hospital and same ST was only 10 alleles
from the outbreak cluster, showing how narrow the gap can be
(Dabernig-Heinz et al. 2024).

**4. Account for how long the source was contaminated.** Bacteria keep
mutating while they persist in a sink, so the longer the interval between
samples, the more differences are expected even from a single source. Fixed
thresholds ignore mutation rate and duration of contamination
(Duval, Opatowski & Brisse 2023).

**5. Sinks hold mixed, long-lived populations.** A single drain can carry
several strains of the same species, so one colony may miss the strain that
reached the patient; picking several colonies per sample helps
(Constantinides et al. 2020). Clones can persist in plumbing for years:
carbapenemase-producing *C. freundii* clusters linked patients and drains from
2018 to 2021 (Hamerlinck et al. 2023).

**6. Genomics cannot tell you the direction.** In a review of ICU sink studies,
sequencing linked sink and patient isolates in about half of cases, but where
timelines were clear they mostly showed patient-to-sink spread; only 8 reports
supported sink-to-patient spread. Direction has to come from sampling dates,
room layout and whether the patient screened negative on admission.

## Thresholds used

Defined in [`assets/schemas.tsv`](assets/schemas.tsv). A pair is
`within_threshold` when its allele differences are at or below the threshold.

| Schema | Organism | Scheme | Loci | Threshold (alleles) | Source |
|---|---|---|---|---|---|
| `paeruginosa` | *P. aeruginosa* | cgmlst.org Paeruginosa | 3,867 | ≤12 | cgmlst.org complex type distance; Tönnies et al. 2021 |
| `kpneumoniae` | *K. pneumoniae* sensu lato | cgmlst.org Kpneumoniae_complex | 2,358 | ≤15 | cgmlst.org complex type distance (SNP alternative: ≤21 SNPs, David et al. 2019) |
| `koxytoca` | *K. oxytoca* species complex | cgmlst.org Koxytoca_complex | 2,536 | ≤6, borderline ≤9 | Dabernig-Heinz et al. 2024 (6 strict, 9 sensitive) |
| `smarcescens` | *S. marcescens* | cgmlst.org Smarcescens | 2,692 | ≤12 | cgmlst.org; Kampmeier et al. 2022 |
| `cfreundii` | *C. freundii* | cgmlst.org Cfreundii | 3,250 | ≤10 | cgmlst.org; Kieninger et al. 2025 |
| `ehormaechei` | *E. hormaechei* | cgmlst.org Ehormaechei | 2,178 | ≤12 | cgmlst.org; Prior et al. 2025 |
| `smaltophilia` | *S. maltophilia* complex | Gröschel et al. 2020 wgMLST | 17,603 | ≤10 | Gröschel et al. 2020 (d10) |

Notes:

- The *P. aeruginosa* paper itself does not state a cut-off; 12 is the complex
  type distance listed on cgmlst.org.
- There is no cgmlst.org scheme for the whole *E. cloacae* complex, only for
  *E. hormaechei*. The `enterobacter_cloacae` isolates are run against it, which
  is only valid if the genome confirms *E. hormaechei*. A 2026 preprint
  describing an *E. cloacae* complex cgMLST found epidemiologically linked
  isolates 0–3 alleles apart.
- For *S. marcescens*, an earlier wgMLST scheme (9,377 loci) used ≤20 alleles,
  with most outbreak isolates ≤4 apart.

## Stenotrophomonas maltophilia wgMLST

No cgmlst.org scheme exists for *S. maltophilia*, so the wgMLST scheme from
Gröschel et al. (2020) is used. It was built by Applied Maths (bioMérieux) from
171 public genomes: overlapping loci, loci with frequent invalid calls, tandem
repeats and multi-copy loci were removed, leaving 17,603 loci (including the
seven classic MLST loci). On average 4,174 loci (range 3,024–4,536) were found
per genome. The allele sequences are published on
[figshare](https://figshare.com/articles/dataset/Smaltophilia_wgMLST_all-alleles_fasta_gz/10005047)
as a single FASTA, which [`bin/split_alleles.py`](bin/split_alleles.py) splits
into one file per locus for chewBBACA.

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

This repository counts differences over all wgMLST loci called in both isolates
(the paper's list of 1,275 core loci is in its supplementary data). Over the
5 days between the Transmission_2 samples, a genuine link should be close to
0 differences; a count near 10 is borderline and worth checking with SNPs
(e.g. SKA2).

## Installation

Requirements: GNU Make, bash, Python 3 (standard library only), `wget`,
`unzip`, `gzip`, and Apptainer or Singularity.

```bash
git clone git@github.com:ryanjameskennedy/sinklink.git
cd sinklink
make print_paths
```

Download the containers, the GAMBIT database and set up all schemas:

```bash
make install ASSETS_DIR=/mnt/cache/dbs/vask CONTAINERS_DIR=/mnt/cache/singularity
```

Or step by step:

```bash
make -C containers all CONTAINERS_DIR=/mnt/cache/singularity
make databases ASSETS_DIR=/mnt/cache/dbs/vask
make schemas ASSETS_DIR=/mnt/cache/dbs/vask CONTAINERS_DIR=/mnt/cache/singularity
make check ASSETS_DIR=/mnt/cache/dbs/vask
```

### Containers

All container URLs and versions are the same as in JASEN, so on thedonkey
`CONTAINERS_DIR=/mnt/cache/singularity` already holds most of them and make
only fetches what is missing.

| Container | Version | Used for |
|---|---|---|
| `trimmomatic.sif` | 0.40 | Illumina trimming (`--trim`) |
| `fastqc.sif` | 0.12.1 | Illumina read QC |
| `filtlong.sif` | 0.3.1 | Nanopore read filtering (`--filtlong`) |
| `nanoplot.sif` | 1.46.2 | Nanopore read QC |
| `skesa.sif` | 2.5.1 | Illumina assembly (default) |
| `spades.sif` | 3.15.5 | Illumina assembly (`--assembler spades`) |
| `flye.sif` | 2.9.6 | Nanopore assembly |
| `medaka.sif` | ontresearch/medaka (JASEN pin) | Nanopore polishing; built from Docker |
| `quast.sif` | 5.2.0 | Assembly statistics |
| `gambitcore.sif` | 0.0.2 | Assembly completeness; built from Docker |
| `bwakit.sif` | 0.7.17 | Mapping Illumina reads back to the assembly |
| `minimap2.sif` | 2.30 | Mapping Nanopore reads back to the assembly |
| `samtools.sif` | 1.17 | Sorting and depth |
| `mlst.sif` | 2.23.0 | 7-gene MLST |
| `kraken2.sif`, `bracken.sif` | Kraken2 (JASEN's mulled image), Bracken 2.8 | Read-based species check |
| `chewbbaca.sif` | 3.5.4 | Allele calling and schema prep |
| `prodigal.sif` | 2.6.3 | Prodigal training files |

### Databases

- **GAMBIT** (for gambitcore): `make gambit_db` downloads the RefSeq curated
  1.0 database into `<assets>/gambit_db`, as JASEN does. On thedonkey use the
  existing `/mnt/cache/dbs/gambit_db`.
- **Kraken2/Bracken**: too large to download here. Point the pipeline at an
  existing database with `--kraken-db`; on thedonkey this is
  `/mnt/cache/dbs/kraken2/standard_2025-06` (the JASEN one). Bracken needs the
  database's `database<length>mers.kmer_distrib` file for `--bracken-read-length`
  (default 150).

### Schemas

A single organism can be set up on its own with `make <schema>_all`
(e.g. `make paeruginosa_all`). For each schema the Makefile:

1. downloads the scheme's seed genome from NCBI;
2. trains Prodigal on it (`assets/prodigal_training_files/<schema>.trn`);
3. downloads the alleles (cgmlst.org or figshare) and records the download date
   in `schemas/<schema>/download/SOURCE`;
4. unpacks them (or splits the single *S. maltophilia* FASTA);
5. runs `chewie PrepExternalSchema` into `schemas/<schema>/alleles_rereffed`.

`PREP_CPUS` (default 4) sets the threads for PrepExternalSchema, and
`APPTAINER=singularity` switches the container runtime.

If a download fails (the cgmlst.org Serratia link can be slow and figshare may
block automated downloads), the Makefile prints the path to save a
browser download to. Save the file there and re-run make.

## Running

Make a reads sheet (CSV) with one row per isolate, using the same IDs as
`translation_id` in the samplesheet
(see [`assets/reads_example.csv`](assets/reads_example.csv)):

```
id,platform,read1,read2
S01,illumina,/data/reads/S01_R1.fastq.gz,/data/reads/S01_R2.fastq.gz
S02,nanopore,/data/reads/S02.fastq.gz,
```

`platform` is `illumina` or `nanopore`. Leave `read2` empty for Nanopore or
single-end Illumina reads. Then on thedonkey:

```bash
bin/sinklink.sh \
    --reads reads.csv \
    --outdir /media/Lagring/$USER/vask \
    --assets /mnt/cache/dbs/vask \
    --containers /mnt/cache/singularity \
    --kraken-db /mnt/cache/dbs/kraken2/standard_2025-06 \
    --gambit-db /mnt/cache/dbs/gambit_db
```

| Option | Meaning | Default |
|---|---|---|
| `--reads FILE` | Reads sheet (`id,platform,read1,read2`) | required |
| `--outdir DIR` | Output folder | required |
| `--samplesheet FILE` | Study samplesheet | `vask_colonisation_hidden.csv` |
| `--assets DIR` | Assets folder containing `schemas/` | `assets/` |
| `--containers DIR` | Folder with the `.sif` images | `containers/` |
| `--kraken-db DIR` | Kraken2/Bracken database; species check skipped without it | none |
| `--gambit-db DIR` | GAMBIT database for gambitcore | `<assets>/gambit_db` if present |
| `--threads INT` | Total threads | 15 |
| `--memory INT` | Total memory (GB) | 141 |
| `--sample-threads INT` | Threads per isolate during assembly and QC | 5 |
| `--assembler NAME` | `skesa` or `spades` (Illumina) | `skesa` |
| `--trim` | Trim Illumina reads with Trimmomatic (`LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36`) | off |
| `--filtlong` | Filter Nanopore reads with Filtlong (`--min_length 1000 --min_mean_q 90`) | off |
| `--bracken-read-length INT` | Bracken k-mer distribution read length | 150 |
| `--skip-chewbbaca` | Stop after assembly and QC | off |
| `-f`, `--force` | Re-run steps even if their output exists | off |
| `-n`, `--dry-run` | Print the commands without running them | off |

The defaults of 15 threads and 141 GB match the caps set for thedonkey
(20 threads and 188 GB, shared with colleagues). Each step writes its output
under a temporary name and moves it into place when it succeeds, so re-running
the same command resumes where it stopped; use `--force` to redo everything.
A failed isolate does not stop the others.

The QC summary and distance check can also be run on their own:

```bash
python3 bin/summarise_qc.py --reads reads.csv \
    --samplesheet vask_colonisation_hidden.csv --results /media/Lagring/$USER/vask \
    --species-map assets/species_map.tsv --schemas assets/schemas.tsv \
    --thresholds assets/qc_thresholds.tsv

python3 bin/check_distances.py \
    --samplesheet vask_colonisation_hidden.csv \
    --results /media/Lagring/$USER/vask/chewbbaca --outdir /media/Lagring/$USER/vask \
    --species-map assets/species_map.tsv --schemas assets/schemas.tsv \
    --qc-summary /media/Lagring/$USER/vask/qc_summary.tsv
```

## Pipeline steps

**Stage 1, per isolate** (`bin/process_sample.sh`). Several isolates run at
once with `xargs -P`: `--threads / --sample-threads` of them (3 by default),
each with an equal share of `--memory`.

| Step | Illumina | Nanopore |
|---|---|---|
| Read filtering (optional) | Trimmomatic | Filtlong |
| Read QC | FastQC | NanoPlot |
| Assembly | SKESA (`--cores --memory`) or SPAdes (`--isolate`) | Flye (`--nano-hq`, `--asm-coverage 50` with the schema's genome size), then two rounds of `medaka_consensus --bacteria` as in JASEN |
| Assembly statistics | QUAST | QUAST |
| Completeness | gambitcore | gambitcore |
| Read depth | `bwa mem` to the isolate's own assembly, `samtools coverage` | `minimap2 -x lr:hq` to the isolate's own assembly, `samtools coverage` |
| 7-gene MLST | `mlst` (scheme detected automatically) | `mlst` |

**Stage 2, species check.** Kraken2 (`--memory-mapping`) and Bracken (species
level) on the reads that went into the assembly, one isolate at a time with all
threads, since the standard database needs most of the machine's memory. If
Bracken fails, the Kraken2 report is used instead.

**Stage 3, allele calling.** Each assembly with a schema is linked into
`chewbbaca/<schema>/genomes/`, and one `chewie AlleleCall` job per schema runs
at the same time with `xargs -P`, splitting the threads evenly. AlleleCall uses
`--no-inferred`, so schemas are never modified; this makes parallel jobs safe
and repeat runs reproducible, and novel alleles are still numbered
consistently within a run. Isolates whose `growth` has no schema are assembled
and QC'd only.

**Stage 4, summaries.** [`bin/summarise_qc.py`](bin/summarise_qc.py) writes
`qc_summary.tsv`, and [`bin/check_distances.py`](bin/check_distances.py)
compares isolates within each transmission group.

## Output

In the output folder:

| Path | Contents |
|---|---|
| `samples/<id>/trimmomatic/`, `filtlong/` | Filtered reads (when enabled) |
| `samples/<id>/fastqc/`, `nanoplot/` | Read QC |
| `samples/<id>/assembly/<id>.fasta` | Final assembly (plus `flye/`, `medaka_round*/` or `spades/`) |
| `samples/<id>/quast/` | QUAST report (`transposed_report.tsv`) |
| `samples/<id>/gambitcore/<id>.tsv` | Completeness and closest species |
| `samples/<id>/mapping/` | Reads mapped back to the assembly and `samtools coverage` |
| `samples/<id>/mlst/` | 7-gene MLST (`.tsv` and `.json`) |
| `samples/<id>/kraken/` | Kraken2 report and Bracken species estimates |
| `samples/<id>/logs/` | One log per step |
| `chewbbaca/<schema>/allelecall/` | chewBBACA results (`results_alleles.tsv` etc.) |
| `qc_summary.tsv` | Read and assembly QC per isolate, with flags |
| `allele_qc.tsv` | Loci called per isolate, with the assembly QC status |
| `pairwise_distances.tsv` | Every pair within each transmission group |
| `group_summary.tsv` | One line per transmission group |

`pairwise_distances.tsv` columns: transmission group, both isolates, their
sample types and patients, days apart, schema, loci shared, allele differences,
threshold, verdict, QC status of the pair and notes. Notes list failed QC
flags, different 7-gene STs and pairs sequenced on different platforms.

Allele calls are counted only when both isolates have a valid allele at a
locus. Missing or ambiguous calls (`LNF`, `PLOT3`, `PLOT5`, `ASM`, `ALM`,
`NIPH`, `NIPHEM`, `LOTSC`, `PAMA`) are ignored rather than counted as
differences. Novel alleles keep their `*` prefix so they never match a schema
allele with the same number.

## Quality control

Thresholds live in [`assets/qc_thresholds.tsv`](assets/qc_thresholds.tsv),
with separate values for Illumina and Nanopore and a severity (`fail` or
`warn`) per check. Species and genome size expectations per schema are the
`species_pattern`, `genera`, `genome_size_min_mb` and `genome_size_max_mb`
columns of [`assets/schemas.tsv`](assets/schemas.tsv).

| Check | Illumina | Nanopore | Severity |
|---|---|---|---|
| Mean read depth over the assembly | ≥30× | ≥40× | fail |
| Contigs ≥500 bp (QUAST) | ≤500 | ≤50 | warn |
| N50 | ≥15 kb | ≥100 kb | warn |
| Assembly length inside the schema's expected range | yes | yes | warn |
| gambitcore completeness | ≥90% | ≥90% | warn |
| Bracken fraction of reads from species the schema covers | ≥0.8 | ≥0.8 | fail |
| Largest fraction of reads from a genus outside the schema's genera | ≤0.05 | ≤0.05 | fail |

These are sensible starting points rather than published cut-offs; adjust them
to your lab's validation. The genome size ranges are approximate.

The species check matters most for the species complexes: an
`enterobacter_cloacae` isolate that Bracken calls *E. cloacae* or
*E. asburiae* rather than *E. hormaechei* fails with `species_mismatch`,
because the cgMLST scheme only covers *E. hormaechei*. Likewise the
*K. oxytoca* scheme accepts the whole complex (*K. michiganensis*,
*K. grimontii*, *K. pasteurii*, ...), and the *K. pneumoniae* scheme the
*K. pneumoniae* species complex.

Each isolate gets `qc_status` `pass`, `warn` or `fail` and a list of flags in
`qc_summary.tsv`. A pair's `qc` column is `fail` if either isolate failed (or
had too few loci called), `warn` if either has warnings, and `not_checked` if
no QC summary was found. Distances are still reported for failed pairs, but
should not be trusted until the isolate is re-sequenced or re-assembled.

## Interpreting the results

Pair verdicts:

| Verdict | Meaning |
|---|---|
| `within_threshold` | At or below the species threshold: same strain |
| `borderline` | Between the strict and sensitive thresholds (*K. oxytoca* only) |
| `above_threshold` | Above the threshold: not the same strain |
| `missing_profile` | One or both isolates have no allele profile |
| `different_schema` | The two isolates were typed with different schemas |

Allele QC (`allele_qc.tsv`): for cgMLST schemas an isolate fails with
`low_calls` if fewer than 90% of loci are called. The wgMLST
*S. maltophilia* scheme has no fraction cut-off, since each genome contains
only about a quarter of its loci.

Group summaries: `all_pairs_within`, `some_pairs_within`, `no_pairs_within`,
or `incomplete` when profiles are missing.

A practical reading for each pair:

1. Did both isolates pass QC? If not, fix that first.
2. Same species and lineage (same 7-gene ST)? If not, no link.
3. Within the threshold? Then the isolates are **genomically linked**.
4. Do the dates and room support the sink as the source (sink positive first,
   patient negative on admission)? Only then call it **probable
   sink-to-patient transmission**. Same-day samples or a patient positive
   before the sink fit patient-to-sink spread equally well.

For groups spanning months (Transmission_3, Transmission_4), expect more
differences than in a short outbreak even from a single persisting source.

## Caveats

- Thresholds are tied to their scheme and software. chewBBACA counts will not
  exactly match Ridom SeqSphere+ or BioNumerics, so treat cut-offs as guides
  and check borderline pairs with SNPs.
- Nanopore assemblies can carry homopolymer and methylation-related errors
  that show up as extra allele differences, especially in pairs where one
  isolate is Illumina and the other Nanopore. Nanopore genotyping can match
  Illumina with recent chemistry and basecalling (Prior et al. 2025), but
  treat mixed-platform pairs near the threshold with care. These pairs are
  flagged in the notes.
- A single colony per sample may not represent a mixed sink population.
- The *E. hormaechei* scheme only applies once the species is confirmed.
- The *S. maltophilia* FASTA header format is assumed to be
  `<locus>_<allele>`; `split_alleles.py` stops if it does not find about
  17,603 loci, and `--pattern` can be set to match another format.
- cgmlst.org allele sets grow over time; the download date is recorded in
  `schemas/<schema>/download/SOURCE`.
- Re-running without `--force` keeps existing chewBBACA results, even if
  assemblies were added or changed; use `--force` after re-assembling.

## Repository layout

```
.
├── Makefile                    # Schema and database setup (seed genome, Prodigal training, download, prep)
├── containers/Makefile         # Container downloads (same URLs as JASEN)
├── assets/
│   ├── schemas.tsv             # Thresholds, expected species and genome size per schema
│   ├── species_map.tsv         # Lab growth label -> schema
│   ├── qc_thresholds.tsv       # Read and assembly QC thresholds per platform
│   └── reads_example.csv       # Example reads sheet
└── bin/
    ├── sinklink.sh             # Runs everything: assembly and QC, species check, AlleleCall, summaries
    ├── process_sample.sh       # Read QC, assembly and assembly QC for one isolate
    ├── summarise_qc.py         # QC summary and flags per isolate
    ├── check_distances.py      # Pairwise distances within transmission groups
    └── split_alleles.py        # Splits a single allele FASTA into one file per locus
```

The samplesheet (`vask_colonisation_hidden.csv`) is git-ignored.

## References

- Constantinides B, et al. Genomic surveillance of *Escherichia coli* and *Klebsiella* spp. in hospital sink drains and patients. *Microb Genom* 2020. [PMC7478627](https://pmc.ncbi.nlm.nih.gov/articles/PMC7478627)
- Dabernig-Heinz J, et al. Core genome multilocus sequence typing (cgMLST) applicable to the monophyletic *Klebsiella oxytoca* species complex. *J Clin Microbiol* 2024;62:e01725-23. [PMC11237601](https://pmc.ncbi.nlm.nih.gov/articles/PMC11237601/)
- David S, et al. Epidemic of carbapenem-resistant *Klebsiella pneumoniae* in Europe is driven by nosocomial spread. *Nat Microbiol* 2019;4:1919–1929.
- Duval A, Opatowski L, Brisse S. Defining genomic epidemiology thresholds for common-source bacterial outbreaks: a modelling study. *Lancet Microbe* 2023;4:e349–e357.
- Gröschel MI, et al. The phylogenetic landscape and nosocomial spread of the multidrug-resistant opportunist *Stenotrophomonas maltophilia*. *Nat Commun* 2020;11:2044. [doi:10.1038/s41467-020-15123-0](https://doi.org/10.1038/s41467-020-15123-0)
- Hamerlinck H, et al. Sanitary installations and wastewater plumbing as reservoir for the long-term circulation and transmission of carbapenemase producing *Citrobacter freundii* clones in a hospital setting. *Antimicrob Resist Infect Control* 2023;12:58. [PMC10280848](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10280848/)
- Kampmeier S, et al. Development and evaluation of a core genome multilocus sequencing typing (cgMLST) scheme for *Serratia marcescens* molecular surveillance and outbreak investigations. *J Clin Microbiol* 2022;60:e01196-22.
- Kieninger B, et al. Development and validation of a core genome multilocus sequence typing scheme for *Citrobacter freundii*. *J Clin Microbiol* 2025;63:e00860-25.
- Prior K, et al. Accurate and reproducible whole-genome genotyping for bacterial genomic surveillance with Nanopore sequencing data. *J Clin Microbiol* 2025;63:e00369-25.
- Tönnies H, Prior K, Harmsen D, Mellmann A. Establishment and evaluation of a core genome multilocus sequence typing scheme for whole-genome sequence-based typing of *Pseudomonas aeruginosa*. *J Clin Microbiol* 2021;59:e01987-20. [PMC8106710](https://pmc.ncbi.nlm.nih.gov/articles/PMC8106710/)
- Ridom cgMLST.org schema list: <https://www.cgmlst.org/ncs>
- Review of ICU sink studies (sink-to-patient vs patient-to-sink): <https://mdpi.com/2673-947X/2/2/8>
