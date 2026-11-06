# Caveats

- **Thresholds belong to their scheme and software.** chewBBACA counts will not
  exactly match Ridom SeqSphere+ or BioNumerics, so treat cut-offs as guides
  and check borderline pairs with SNPs.
- **Mixed platforms.** Nanopore assemblies can carry homopolymer and
  methylation-related errors that show up as extra allele differences,
  especially in pairs where one isolate is Illumina and the other Nanopore.
  Nanopore genotyping can match Illumina with recent chemistry and basecalling
  (Prior et al. 2025), but treat mixed-platform pairs near the threshold with
  care. These pairs are flagged in the notes.
- **One colony per sample** may not represent a mixed sink population.
- **The *E. hormaechei* scheme** only applies once the species is confirmed.
- **The *S. maltophilia* FASTA header format** is assumed to be
  `<locus>_<allele>`; `split_alleles.py` stops if it does not find about
  17,603 loci.
- **cgmlst.org allele sets grow over time**; the download date is recorded in
  `schemas/<schema>/download/SOURCE`.
- **Tool versions** come from the nf-core modules and differ from JASEN's in
  places (e.g. Flye 2.9.5, QUAST 5.3.0, SPAdes 4.1.0); chewBBACA is pinned to
  3.5.4 to match schema prep.
