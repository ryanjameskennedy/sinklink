#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
    cat <<EOF
Run chewBBACA AlleleCall on every isolate in the samplesheet, one job per
schema in parallel, then compare isolates within each transmission group.

Usage: $(basename "$0") -a ASSEMBLY_DIR -o OUTDIR [options]

Required:
  -a DIR   folder of assemblies named <translation_id>.{fasta,fa,fna}[.gz]
  -o DIR   output folder

Options:
  -s FILE  samplesheet (default: $REPO_DIR/vask_colonisation_hidden.csv)
  -d DIR   assets folder holding schemas/ (default: $REPO_DIR/assets)
  -c DIR   folder with chewbbaca.sif (default: $REPO_DIR/containers)
  -t INT   total threads to use (default: 15, the cap on thedonkey)
  -f       re-run AlleleCall even if results already exist
  -n       dry run: stage inputs and print the commands without running them
  -h       show this help

Example on thedonkey:
  $(basename "$0") -a /media/Lagring/$USER/jasen/assemblies \\
      -o /media/Lagring/$USER/vask -d /mnt/cache/dbs/vask -c /mnt/cache/singularity
EOF
}

SAMPLESHEET="$REPO_DIR/vask_colonisation_hidden.csv"
ASSETS_DIR="$REPO_DIR/assets"
CONTAINERS_DIR="$REPO_DIR/containers"
THREADS=15
FORCE=0
DRY_RUN=0
ASSEMBLY_DIR=""
OUTDIR=""

while getopts "a:o:s:d:c:t:fnh" opt; do
    case "$opt" in
        a) ASSEMBLY_DIR="$OPTARG" ;;
        o) OUTDIR="$OPTARG" ;;
        s) SAMPLESHEET="$OPTARG" ;;
        d) ASSETS_DIR="$OPTARG" ;;
        c) CONTAINERS_DIR="$OPTARG" ;;
        t) THREADS="$OPTARG" ;;
        f) FORCE=1 ;;
        n) DRY_RUN=1 ;;
        h) usage; exit 0 ;;
        *) usage >&2; exit 1 ;;
    esac
done

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[$(date "+%Y-%m-%d %H:%M:%S")] $*"; }

[[ -n "$ASSEMBLY_DIR" && -n "$OUTDIR" ]] || { usage >&2; exit 1; }
[[ -d "$ASSEMBLY_DIR" ]] || die "assembly folder not found: $ASSEMBLY_DIR"
[[ -f "$SAMPLESHEET" ]] || die "samplesheet not found: $SAMPLESHEET"
[[ "$THREADS" =~ ^[1-9][0-9]*$ ]] || die "-t must be a positive integer"

SPECIES_MAP="$REPO_DIR/assets/species_map.tsv"
SCHEMA_TABLE="$REPO_DIR/assets/schemas.tsv"
[[ -d "$ASSETS_DIR" ]] || die "assets folder not found: $ASSETS_DIR"
SCHEMAS_DIR="$(cd "$ASSETS_DIR" && pwd)/schemas"
CHEWBBACA_SIF="$CONTAINERS_DIR/chewbbaca.sif"
mkdir -p "$OUTDIR"
OUTDIR="$(cd "$OUTDIR" && pwd)"

if command -v apptainer > /dev/null; then
    APPTAINER=apptainer
elif command -v singularity > /dev/null; then
    APPTAINER=singularity
elif [[ $DRY_RUN -eq 1 ]]; then
    APPTAINER=apptainer
else
    die "neither apptainer nor singularity is on PATH"
fi
[[ $DRY_RUN -eq 1 || -e "$CHEWBBACA_SIF" ]] || die "container not found: $CHEWBBACA_SIF (run make -C containers)"

abs_path() {
    if [[ -d "$1" ]]; then (cd "$1" && pwd); elif [[ "$1" == /* ]]; then echo "$1"; else echo "$PWD/$1"; fi
}
top_dir() { echo "/$(echo "$1" | cut -d/ -f2)"; }
BIND_ARGS=""
for root in $(printf '%s\n' "$(top_dir "$OUTDIR")" "$(top_dir "$SCHEMAS_DIR")" \
        "$(top_dir "$(abs_path "$CONTAINERS_DIR")")" | sort -u); do
    BIND_ARGS+=" --bind $root"
done

schema_for() {
    awk -F'\t' -v g="$1" 'NR > 1 && $1 == g { print $2; exit }' "$SPECIES_MAP"
}

find_assembly() {
    local id="$1" ext
    for ext in fasta fa fna fasta.gz fa.gz fna.gz; do
        if [[ -f "$ASSEMBLY_DIR/$id.$ext" ]]; then
            echo "$ASSEMBLY_DIR/$id.$ext"
            return
        fi
    done
}

log "Staging assemblies from $ASSEMBLY_DIR"
rm -rf "$OUTDIR"/*/genomes
missing=0
while IFS=$'\t' read -r id growth; do
    schema="$(schema_for "$growth")"
    if [[ -z "$schema" ]]; then
        echo "  WARNING: no schema mapped for growth '$growth' ($id); add it to $SPECIES_MAP" >&2
        continue
    fi
    assembly="$(find_assembly "$id")"
    if [[ -z "$assembly" ]]; then
        echo "  WARNING: no assembly found for $id in $ASSEMBLY_DIR" >&2
        missing=$((missing + 1))
        continue
    fi
    genomes="$OUTDIR/$schema/genomes"
    mkdir -p "$genomes"
    if [[ "$assembly" == *.gz ]]; then
        gunzip -c "$assembly" > "$genomes/$id.fasta"
    else
        cp "$assembly" "$genomes/$id.fasta"
    fi
done < <(awk -F',' '
    NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
    { print $col["translation_id"] "\t" $col["growth"] }
' "$SAMPLESHEET")
[[ $missing -eq 0 ]] || log "$missing isolate(s) have no assembly and will be skipped"

schemas=()
for genomes in "$OUTDIR"/*/genomes; do
    [[ -d "$genomes" ]] || continue
    schema="$(basename "$(dirname "$genomes")")"
    if [[ ! -d "$SCHEMAS_DIR/$schema/alleles_rereffed" ]]; then
        echo "  WARNING: schema $schema is not set up in $SCHEMAS_DIR (run make ${schema}_all); skipping" >&2
        continue
    fi
    schemas+=("$schema")
done
[[ ${#schemas[@]} -gt 0 ]] || die "nothing to run"

jobs=${#schemas[@]}
(( jobs > THREADS )) && jobs=$THREADS
cpus_per_job=$(( THREADS / jobs ))
log "Running AlleleCall for ${#schemas[@]} schema(s): ${schemas[*]}"
log "$jobs job(s) at a time, $cpus_per_job thread(s) each"

run_allelecall() {
    local schema="$1"
    local result_dir="$OUTDIR/$schema/allelecall"
    local cmd=("$APPTAINER" exec $BIND_ARGS "$CHEWBBACA_SIF"
        chewie AlleleCall
        -i "$OUTDIR/$schema/genomes"
        -g "$SCHEMAS_DIR/$schema/alleles_rereffed"
        -o "$result_dir"
        --cpu "$CPUS_PER_JOB"
        --no-inferred)

    if [[ $FORCE -eq 0 && -n "$(find "$result_dir" -name results_alleles.tsv 2> /dev/null)" ]]; then
        echo "[$schema] results exist, skipping (use -f to re-run)"
        return 0
    fi
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "[$schema] ${cmd[*]}"
        return 0
    fi
    rm -rf "$result_dir"
    echo "[$schema] started $(date "+%H:%M:%S"), log: $OUTDIR/$schema/allelecall.log"
    if "${cmd[@]}" > "$OUTDIR/$schema/allelecall.log" 2>&1; then
        echo "[$schema] finished $(date "+%H:%M:%S")"
    else
        echo "[$schema] FAILED, see $OUTDIR/$schema/allelecall.log" >&2
        return 1
    fi
}

export -f run_allelecall
export OUTDIR SCHEMAS_DIR CHEWBBACA_SIF APPTAINER BIND_ARGS FORCE DRY_RUN
export CPUS_PER_JOB=$cpus_per_job

status=0
printf '%s\n' "${schemas[@]}" | xargs -P "$jobs" -I{} bash -c 'run_allelecall "$1"' _ {} || status=$?
[[ $status -eq 0 ]] || log "One or more AlleleCall jobs failed; distances are only computed for the ones that finished"

[[ $DRY_RUN -eq 1 ]] && exit 0

log "Comparing isolates within transmission groups"
python3 -I "$REPO_DIR/bin/check_distances.py" \
    --samplesheet "$SAMPLESHEET" \
    --results "$OUTDIR" \
    --species-map "$SPECIES_MAP" \
    --schemas "$SCHEMA_TABLE"

exit $status
