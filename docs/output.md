# sinklink: Output

## Introduction

This document describes the output produced by the pipeline. Most of the plots are taken from the MultiQC report, which summarises results at the end of the pipeline.

The directories listed below will be created in the results directory after the pipeline has finished. All paths are relative to the top-level results directory.

## Pipeline overview

The pipeline is built using [Nextflow](https://www.nextflow.io/) and processes data using the following steps:

- [Read preparation](#read-preparation) - Human read removal with Deacon, optional Trimmomatic or Filtlong, then FastQC or NanoPlot
- [Assembly](#assembly) - SKESA (Illumina), Flye and Medaka (Nanopore)
- [Assembly QC](#assembly-qc) - QUAST and Mash against the reference genome, gambitcore, read depth and 7-gene MLST
- [Species check](#species-check) - Kraken2 and Bracken on the reads
- [Variant calling](#variant-calling) - Snippy (Illumina) or minimap2 and Clair3 (Nanopore) against the reference genome
- [Allele calling](#allele-calling) - chewBBACA AlleleCall per schema
- [Summary](#summary) - QC summary and allele and SNP distances within transmission groups
- [Transmission report](#transmission-report) - HTML report and publication figures
- [MultiQC](#multiqc) - Aggregate report describing results and QC from the whole pipeline
- [Pipeline information](#pipeline-information) - Report metrics generated during the workflow execution

### Read preparation

<details markdown="1">
<summary>Output files</summary>

- `host_removal/<sample>.host_removed.json`: Deacon summary with the number of reads in and out.
- `host_removal/<sample>.host_removed*.fq.gz`: reads without human reads (with `--save_host_removed_reads`).
- `trimmomatic/`: `*.summary` and `*_out.log` per isolate (with `--trim`).
- `filtlong/`: `*.log` per isolate (with `--filtlong`).
- `fastqc/`: `*.html` and `*.zip` per Illumina isolate.
- `nanoplot/<sample>/`: NanoPlot report and `NanoStats.txt` per Nanopore isolate.

</details>

Deacon removes reads that match the human pangenome index before anything else, so every later step, and any reads you archive or share, is free of human DNA. Cultured isolates carry few human reads, so the main gain is privacy. FastQC and NanoPlot summarise read quality and length. Filtered reads are not published; they stay in the work directory.

### Assembly

<details markdown="1">
<summary>Output files</summary>

- `assembly/<sample>.fa`: the final assembly used for QC and allele calling.
- `assembly/flye/`: Flye assembly graph, info and log (Nanopore).

</details>

Illumina reads are assembled with SKESA. Nanopore reads are assembled with Flye `--nano-hq` (with `--asm-coverage 50` and the schema's expected genome size) and polished once with `medaka_consensus --bacteria`.

### Assembly QC

<details markdown="1">
<summary>Output files</summary>

- `quast/<sample>.quast/`: QUAST report (`report.tsv`, `report.html`, ...), including genome fraction and aligned statistics against the schema's reference genome.
- `mash/<sample>.mash.txt`: Mash distance from the assembly to the schema's reference genome.
- `gambitcore/<sample>.gambitcore.tsv`: closest species, completeness and a green/amber/red call (with `--gambit_db`).
- `coverage/<sample>.coverage.txt`: `samtools coverage` of the reads mapped back to the isolate's own assembly.
- `mlst/<sample>.mlst.tsv`: 7-gene MLST scheme and sequence type.

</details>

Reads are mapped with `bwa mem` (Illumina) or `minimap2 -x lr:hq` (Nanopore); the mean depth weighted by contig length goes into the QC summary. QUAST's misassembly counts against the reference are not used for QC: an isolate is not expected to share the reference's genome structure.

### Species check

<details markdown="1">
<summary>Output files</summary>

- `kraken2/<sample>.kraken2.report.txt`: Kraken2 report.
- `bracken/<sample>.bracken.tsv`: Bracken species-level estimates.

</details>

Always runs; `--kraken_db` is required. If Bracken fails (for example when the database has no k-mer distribution for `--bracken_read_length`), the Kraken2 report is used for the species check instead.

### Variant calling

<details markdown="1">
<summary>Output files</summary>

- `variants/<sample>.vcf.gz`: variant calls against the schema's reference genome, from Snippy (Illumina, with `.csi` index) or Clair3 (Nanopore, with `.tbi` index).
- `variants/<sample>.pseudogenome.fa`: the reference chromosome with the isolate's substitutions applied, and `N` where read depth is below `--snp_min_depth` or the reference has a repeat or prophage.
- `snp_distances/<schema>.aln`: the schema's pseudogenomes and the reference chromosome (`Reference`) in one alignment.
- `snp_distances/gubbins/`: Gubbins output for each schema with 3 or more sequences: recombination predictions, tree and the filtered alignment.
- `snp_distances/<schema>.gubbins.snp_dists.tsv` or `snp_distances/<schema>.snp_dists.tsv`: pairwise SNP distances, with or without recombination removed.
- `snp_distances/masks/<accession>.mask.bed`: repeat and prophage regions of each reference genome, and `<accession>.phispy.tsv`, PhiSpy's prophage coordinates.

</details>

Illumina reads go through Snippy (`bwa mem` and FreeBayes, `--mincov` set by `--snp_min_depth`). Nanopore reads are mapped with `minimap2 -x lr:hq` and called with Clair3 in haploid mode (`--haploid_precise --include_all_ctgs --no_phasing_for_fa`) using `--clair3_model`. Runs unless `--skip_variant_calling` is set.

The SNP distances follow the usual reference-based approach (as in nf-core/bactmap and snippy-core), built from existing tools:

1. Once per reference genome, repeats are found by aligning the genome to itself with MUMmer `nucmer --maxmatch --nosimplify`, and prophages with PhiSpy on its GenBank file. Both are masked after mapping, not before, so reads are still placed against the whole genome.
2. Per isolate, `bcftools view` keeps PASS SNPs and MNPs with an alternative genotype, mosdepth finds the regions below `--snp_min_depth`, and `bcftools consensus` applies the SNPs to the reference with the low-depth, repeat and prophage regions set to `N`. Only the chromosome is kept; plasmids move between strains and are left out of SNP comparisons. Indels are not used.
3. Per schema, the pseudogenomes and the reference chromosome are joined into one alignment. With 3 or more sequences, Gubbins removes SNPs in recombinant regions; snp-dists then counts the differences between each pair, ignoring `N`.

### Allele calling

<details markdown="1">
<summary>Output files</summary>

- `chewbbaca/<schema>/<schema>_results_alleles.tsv`: allele profiles of every isolate typed with that schema.
- `chewbbaca/<schema>/<schema>_results_statistics.tsv`, `*_results_contigsInfo.tsv`, ...: chewBBACA statistics and logs.

</details>

One AlleleCall job per schema, run with `--no-inferred` so the schemas are never modified.

### Summary

<details markdown="1">
<summary>Output files</summary>

- `summary/qc_summary.tsv`: read and assembly QC per isolate with `qc_status` (`pass`, `warn` or `fail`) and `qc_flags`.
- `summary/allele_qc.tsv`: loci called per isolate and its assembly QC status.
- `summary/pairwise_distances.tsv`: every pair within each transmission group: sample IDs, LIMS IDs, sample types and patients, days apart, schema, loci shared, allele differences, threshold, verdict, SNP distance and whether recombination was removed, pair QC and notes.
- `summary/group_summary.tsv`: one line per transmission group, with the smallest and largest allele and SNP distances.

</details>

See [quality control](pipeline/qc.md) for the QC flags and [interpreting the results](results/interpreting.md) for the verdicts and how to read a pair.

### Transmission report

<details markdown="1">
<summary>Output files</summary>

- `report/transmission_report.html`: one self-contained page with the figures, a table of the transmission groups, a section for each group with its timeline, tree and pairs, the isolate QC and the thresholds used. Open it in a browser; it needs no internet connection.
- `report/table1.tsv`: one line per transmission group (species, isolates, environment and patient samples, patients, first and last sample, days, allele and SNP distance ranges, verdict and QC), ready to become Table 1 of a paper.
- `report/figures/`: every figure as PDF, SVG and PNG (`--report_formats`):
  - `distance_overview`: the allele differences of every pair, one row per group and one panel per species, with the threshold and borderline range;
  - `distance_vs_time`: allele differences against the days between the two samples, one panel per species;
  - `allele_vs_snp`: allele differences against SNP differences, one panel per species (only when variant calling ran);
  - `timeline_<group>` and `timelines`: when and where each isolate was sampled, with each isolate joined to the earlier isolate it is closest to when that pair is within the threshold;
  - `tree_<group>` and `trees`: a minimum spanning tree of each group with three or more isolates;
  - `isolate_qc`: read depth, species purity, contamination and loci called per isolate against the QC cut-offs.

</details>

The figures are sized for a journal page (180 mm wide by default), use colours
that stay distinct for colour-blind readers and keep their text editable in the
PDF and SVG files. Environmental samples are the ones whose `sample_type` is in
`--report_environment_types` (default `environment`); every other sample type
counts as a patient sample. See
[interpreting the results](results/interpreting.md#transmission-report) for how
to read the figures.

To restyle the figures for a journal without rerunning the pipeline, run the
script on a finished results folder. It needs Python 3 with matplotlib, or the
report container:

```bash
python3 bin/transmission_report.py \
    --pairs results/summary/pairwise_distances.tsv \
    --groups results/summary/group_summary.tsv \
    --allele-qc results/summary/allele_qc.tsv \
    --qc-summary results/summary/qc_summary.tsv \
    --metadata metadata.csv \
    --schemas assets/schemas.tsv \
    --qc-thresholds assets/qc_thresholds.tsv \
    --outdir paper_figures \
    --formats pdf,png --width-mm 88 --font-size 6
```

`--width-mm` sets the width of full-width figures (88 mm is a single journal
column) and `--font-size` the base font size in points. The figures use Arial
or Helvetica when installed, otherwise Liberation Sans or DejaVu Sans; the
container only has DejaVu Sans, so run the script locally if the journal asks
for Arial.

### MultiQC

<details markdown="1">
<summary>Output files</summary>

- `multiqc/`
  - `multiqc_report.html`: a standalone HTML file that can be viewed in your web browser.
  - `multiqc_data/`: directory containing parsed statistics from the different tools used in the pipeline.
  - `multiqc_plots/`: directory containing static images from the report in various formats.

</details>

[MultiQC](http://multiqc.info) is a visualization tool that generates a single HTML report summarising all samples in your project. Most of the pipeline QC results are visualised in the report and further statistics are available in the report data directory.

Results generated by MultiQC collate pipeline QC from supported tools e.g. FastQC. The pipeline has special steps which also allow the software versions to be reported in the MultiQC output for future traceability. For more information about how to use MultiQC reports, see <http://multiqc.info>.

### Pipeline information

<details markdown="1">
<summary>Output files</summary>

- `pipeline_info/`
  - Reports generated by Nextflow: `execution_report.html`, `execution_timeline.html`, `execution_trace.txt` and `pipeline_dag.dot`/`pipeline_dag.svg`.
  - Reports generated by the pipeline: `pipeline_report.html`, `pipeline_report.txt` and `software_versions.yml`. The `pipeline_report*` files will only be present if the `--email` / `--email_on_fail` parameter's are used when running the pipeline.
  - Reformatted samplesheet files used as input to the pipeline: `samplesheet.valid.csv`.
  - Parameters used by the pipeline run: `params.json`.

</details>

[Nextflow](https://www.nextflow.io/docs/latest/tracing.html) provides excellent functionality for generating various reports relevant to the running and execution of the pipeline. This will allow you to troubleshoot errors with the running of the pipeline, and also provide you with other information such as launch commands, run times and resource usage.
