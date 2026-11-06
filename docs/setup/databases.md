# Databases

Both databases are optional; without them the matching check is skipped and
flagged in the QC summary.

## GAMBIT (completeness)

gambitcore estimates assembly completeness against the core k-mers of the
closest species in the GAMBIT RefSeq curated 1.0 database. `make gambit_db`
downloads it into `<ASSETS_DIR>/gambit_db`, as JASEN does. Pass the folder with
`--gambit_db`.

## Kraken2/Bracken (species check)

The standard Kraken2 database is too large to download as part of the setup.
Point the pipeline at an existing one with `--kraken_db`. Bracken needs the
database's `database<length>mers.kmer_distrib` file for the read length given
with `--bracken_read_length` (default 150); if Bracken fails, the Kraken2
report is used instead.

On thedonkey both are set by the [thedonkey profile](thedonkey.md).
