# Schemas

`make schemas` sets up every schema listed in the
[species table](../species/index.md); `make <schema>_all` (e.g.
`make paeruginosa_all`) sets up one. For each schema the Makefile:

1. downloads the scheme's seed genome from NCBI;
2. trains Prodigal on it (`assets/prodigal_training_files/<schema>.trn`);
3. downloads the alleles (cgmlst.org or figshare) and records the download date
   in `schemas/<schema>/download/SOURCE`;
4. unpacks them (or splits the single _S. maltophilia_ FASTA into one file per
   locus with `bin/split_alleles.py`);
5. runs `chewie PrepExternalSchema` (chewBBACA 3.5.4) into
   `schemas/<schema>/alleles_rereffed`.

Pass `<ASSETS_DIR>/schemas` to the pipeline as `--schemas_dir`.

| Variable         | Default       | Meaning                                           |
| ---------------- | ------------- | ------------------------------------------------- |
| `ASSETS_DIR`     | `assets/`     | Where schemas, seed genomes and training files go |
| `CONTAINERS_DIR` | `containers/` | Where `chewbbaca.sif` and `prodigal.sif` are      |
| `PREP_CPUS`      | 4             | Threads for PrepExternalSchema                    |
| `APPTAINER`      | `apptainer`   | Set to `singularity` to switch runtime            |

`make check` lists which schemas are ready and how many loci each has.

## When a download fails

The cgmlst.org Serratia link can be slow and figshare may block automated
downloads. The Makefile then prints the path to save the file to: download it
in a browser, save it there and re-run make.

cgmlst.org allele sets grow over time, so the download date in `SOURCE` matters
for reproducibility.
