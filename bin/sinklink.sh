#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
    cat <<EOF
Assemble and QC every isolate, call alleles with chewBBACA and compare isolates
within each transmission group. Runs on a single machine without a scheduler.

Usage: $(basename "$0") --reads FILE --outdir DIR [options]

Required:
  --reads FILE           CSV with columns id,platform,read1,read2 (platform is
                         illumina or nanopore; read2 empty for single-end/ONT)
  --outdir DIR           output folder

Inputs and references:
  --samplesheet FILE     study CSV with translation_id, transmission, growth, ...
                         (default: $REPO_DIR/vask_colonisation_hidden.csv)
  --assets DIR           folder holding schemas/ (default: $REPO_DIR/assets)
  --containers DIR       folder with the .sif images (default: $REPO_DIR/containers)
  --kraken-db DIR        Kraken2/Bracken database; species check is skipped without it
  --gambit-db DIR        GAMBIT database for gambitcore (default: <assets>/gambit_db if present)

Resources:
  --threads INT          total threads (default: 15, the cap on thedonkey)
  --memory INT           total memory in GB (default: 141, the cap on thedonkey)
  --sample-threads INT   threads per isolate during assembly and QC (default: 5)

Options:
  --assembler NAME       skesa (default) or spades, for Illumina reads
  --trim                 trim Illumina reads with Trimmomatic before assembly
  --filtlong             filter Nanopore reads with Filtlong before assembly
  --bracken-read-length INT
                         read length of the Bracken k-mer distribution (default: 150)
  --skip-chewbbaca       stop after assembly and QC
  -f, --force            re-run steps even if their output exists
  -n, --dry-run          print the commands without running them
  -h, --help             show this help

Example on thedonkey:
  $(basename "$0") --reads reads.csv --outdir /media/Lagring/$USER/vask \\
      --assets /mnt/cache/dbs/vask --containers /mnt/cache/singularity \\
      --kraken-db /mnt/cache/dbs/kraken2/standard_2025-06 --gambit-db /mnt/cache/dbs/gambit_db
EOF
}

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[$(date "+%Y-%m-%d %H:%M:%S")] $*"; }

READS=""
OUTDIR=""
SAMPLESHEET="$REPO_DIR/vask_colonisation_hidden.csv"
ASSETS_DIR="$REPO_DIR/assets"
CONTAINERS_DIR="$REPO_DIR/containers"
KRAKEN_DB=""
GAMBIT_DB=""
THREADS=15
MEMORY=141
SAMPLE_THREADS=5
ASSEMBLER=skesa
TRIM=0
FILTLONG=0
BRACKEN_READ_LENGTH=150
SKIP_CHEWBBACA=0
FORCE=0
DRY_RUN=0
TRIMMOMATIC_ARGS="LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36"
FILTLONG_ARGS="--min_length 1000 --min_mean_q 90"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reads) READS="$2"; shift ;;
        --outdir) OUTDIR="$2"; shift ;;
        --samplesheet) SAMPLESHEET="$2"; shift ;;
        --assets) ASSETS_DIR="$2"; shift ;;
        --containers) CONTAINERS_DIR="$2"; shift ;;
        --kraken-db) KRAKEN_DB="$2"; shift ;;
        --gambit-db) GAMBIT_DB="$2"; shift ;;
        --threads) THREADS="$2"; shift ;;
        --memory) MEMORY="$2"; shift ;;
        --sample-threads) SAMPLE_THREADS="$2"; shift ;;
        --assembler) ASSEMBLER="$2"; shift ;;
        --trim) TRIM=1 ;;
        --filtlong) FILTLONG=1 ;;
        --bracken-read-length) BRACKEN_READ_LENGTH="$2"; shift ;;
        --skip-chewbbaca) SKIP_CHEWBBACA=1 ;;
        -f|--force) FORCE=1 ;;
        -n|--dry-run) DRY_RUN=1 ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; die "unknown option: $1" ;;
    esac
    shift
done

[[ -n "$READS" && -n "$OUTDIR" ]] || { usage >&2; exit 1; }
[[ -f "$READS" ]] || die "reads sheet not found: $READS"
[[ -f "$SAMPLESHEET" ]] || die "samplesheet not found: $SAMPLESHEET"
[[ -d "$ASSETS_DIR" ]] || die "assets folder not found: $ASSETS_DIR"
for value in "$THREADS" "$MEMORY" "$SAMPLE_THREADS" "$BRACKEN_READ_LENGTH"; do
    [[ "$value" =~ ^[1-9][0-9]*$ ]] || die "threads, memory and read length must be positive integers"
done
[[ "$ASSEMBLER" == skesa || "$ASSEMBLER" == spades ]] || die "--assembler must be skesa or spades"
[[ -z "$KRAKEN_DB" || -d "$KRAKEN_DB" ]] || die "Kraken2 database not found: $KRAKEN_DB"
if [[ -z "$GAMBIT_DB" && -d "$ASSETS_DIR/gambit_db" ]]; then
    GAMBIT_DB="$ASSETS_DIR/gambit_db"
fi
[[ -z "$GAMBIT_DB" || -d "$GAMBIT_DB" ]] || die "GAMBIT database not found: $GAMBIT_DB"

abs_path() {
    if [[ -d "$1" ]]; then
        (cd "$1" && pwd)
    elif [[ -e "$1" ]]; then
        echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
    elif [[ "$1" == /* ]]; then
        echo "$1"
    else
        echo "$PWD/$1"
    fi
}
top_dir() { echo "/$(echo "$1" | cut -d/ -f2)"; }

ASSETS_DIR="$(abs_path "$ASSETS_DIR")"
CONTAINERS_DIR="$(abs_path "$CONTAINERS_DIR")"
SCHEMAS_DIR="$ASSETS_DIR/schemas"
[[ -n "$KRAKEN_DB" ]] && KRAKEN_DB="$(abs_path "$KRAKEN_DB")"
[[ -n "$GAMBIT_DB" ]] && GAMBIT_DB="$(abs_path "$GAMBIT_DB")"
SPECIES_MAP="$REPO_DIR/assets/species_map.tsv"
SCHEMA_TABLE="$REPO_DIR/assets/schemas.tsv"
QC_THRESHOLDS="$REPO_DIR/assets/qc_thresholds.tsv"
mkdir -p "$OUTDIR"
OUTDIR="$(abs_path "$OUTDIR")"

if command -v apptainer > /dev/null; then
    APPTAINER=apptainer
elif command -v singularity > /dev/null; then
    APPTAINER=singularity
elif [[ $DRY_RUN -eq 1 ]]; then
    APPTAINER=apptainer
else
    die "neither apptainer nor singularity is on PATH"
fi

# One line per isolate: id|platform|read1|read2|growth|schema|flye genome size
SAMPLES="$OUTDIR/samples.txt"
awk -F'\t' '
    { sub(/\r$/, "") }
    FNR == 1 { file++ }
    file == 1 && FNR > 1 { schema_of[$1] = $2; next }
    file == 2 && FNR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
    file == 2 {
        size = ($(col["genome_size_min_mb"]) + $(col["genome_size_max_mb"])) / 2
        size_of[$(col["schema"])] = sprintf("%.1fm", size)
        next
    }
    file == 3 && FNR == 1 { FS = ","; $0 = $0; for (i = 1; i <= NF; i++) study[$i] = i; next }
    file == 3 { growth_of[$(study["translation_id"])] = $(study["growth"]); next }
    file == 4 && FNR == 1 { FS = ","; $0 = $0; for (i = 1; i <= NF; i++) reads[$i] = i; next }
    file == 4 {
        id = $(reads["id"])
        growth = growth_of[id]
        schema = schema_of[growth]
        print id "|" $(reads["platform"]) "|" $(reads["read1"]) "|" $(reads["read2"]) "|" growth "|" schema "|" size_of[schema]
    }
' "$SPECIES_MAP" "$SCHEMA_TABLE" "$SAMPLESHEET" "$READS" > "$SAMPLES"

bind_roots=("$(top_dir "$OUTDIR")" "$(top_dir "$ASSETS_DIR")" "$(top_dir "$CONTAINERS_DIR")")
[[ -n "$KRAKEN_DB" ]] && bind_roots+=("$(top_dir "$KRAKEN_DB")")
[[ -n "$GAMBIT_DB" ]] && bind_roots+=("$(top_dir "$GAMBIT_DB")")

jobs_file="$OUTDIR/sample_jobs.txt"
: > "$jobs_file"
nsamples=0
has_illumina=0
has_nanopore=0
while IFS='|' read -r id platform read1 read2 growth schema genome_size; do
    [[ -n "$id" ]] || continue
    [[ "$id" =~ ^[A-Za-z0-9._-]+$ ]] || die "isolate ids may only contain letters, digits, '.', '_' and '-': '$id'"
    [[ "$platform" == illumina || "$platform" == nanopore ]] \
        || die "$id: platform must be illumina or nanopore, not '$platform'"
    for read in "$read1" ${read2:+"$read2"}; do
        [[ $DRY_RUN -eq 1 || -f "$read" ]] || die "$id: reads not found: $read"
    done
    if [[ "$platform" == nanopore ]]; then
        [[ -z "$read2" ]] || die "$id: Nanopore reads take read1 only"
        has_nanopore=1
    else
        has_illumina=1
    fi
    read1="$(abs_path "$read1")"
    [[ -n "$read2" ]] && read2="$(abs_path "$read2")"
    bind_roots+=("$(top_dir "$read1")")
    [[ -n "$read2" ]] && bind_roots+=("$(top_dir "$read2")")
    [[ -n "$schema" ]] || echo "  WARNING: $id has no schema (growth '${growth:-not in samplesheet}'); it is assembled and QC'd only" >&2
    printf '%s|%s|%s|%s|%s\n' "$id" "$platform" "$read1" "$read2" "$genome_size" >> "$jobs_file"
    nsamples=$((nsamples + 1))
done < "$SAMPLES"
[[ $nsamples -gt 0 ]] || die "no isolates in $READS"

BIND_ARGS=""
for root in $(printf '%s\n' "${bind_roots[@]}" | sort -u); do
    BIND_ARGS+=" --bind $root"
done

needed=(quast mlst samtools)
[[ $has_illumina -eq 1 ]] && needed+=(fastqc bwakit "$ASSEMBLER")
[[ $has_illumina -eq 1 && $TRIM -eq 1 ]] && needed+=(trimmomatic)
[[ $has_nanopore -eq 1 ]] && needed+=(nanoplot minimap2 flye medaka)
[[ $has_nanopore -eq 1 && $FILTLONG -eq 1 ]] && needed+=(filtlong)
[[ -n "$GAMBIT_DB" ]] && needed+=(gambitcore)
[[ -n "$KRAKEN_DB" ]] && needed+=(kraken2 bracken)
[[ $SKIP_CHEWBBACA -eq 1 ]] || needed+=(chewbbaca)
if [[ $DRY_RUN -eq 0 ]]; then
    for sif in "${needed[@]}"; do
        [[ -e "$CONTAINERS_DIR/$sif.sif" ]] || die "container not found: $CONTAINERS_DIR/$sif.sif (run make -C containers)"
    done
fi

run() {
    local sif="$CONTAINERS_DIR/$1.sif"
    shift
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "    $APPTAINER exec$BIND_ARGS $sif $*"
        return 0
    fi
    $APPTAINER exec $BIND_ARGS "$sif" "$@"
}

overall=0

# ------------------------------------------------------------------------------
# Stage 1: read QC, assembly and assembly QC, several isolates at a time
# ------------------------------------------------------------------------------
(( SAMPLE_THREADS > THREADS )) && SAMPLE_THREADS=$THREADS
jobs=$(( THREADS / SAMPLE_THREADS ))
(( jobs > nsamples )) && jobs=$nsamples
SAMPLE_MEMORY=$(( MEMORY / jobs ))
log "Stage 1: assembly and QC for $nsamples isolate(s), $jobs at a time with $SAMPLE_THREADS threads and ${SAMPLE_MEMORY} GB each"

JOBS_FILE="$jobs_file"
export OUTDIR CONTAINERS_DIR APPTAINER BIND_ARGS SAMPLE_THREADS SAMPLE_MEMORY ASSEMBLER \
    TRIM FILTLONG GAMBIT_DB FORCE DRY_RUN TRIMMOMATIC_ARGS FILTLONG_ARGS JOBS_FILE
status=0
cut -d'|' -f1 "$jobs_file" | xargs -P "$jobs" -n 1 bash "$REPO_DIR/bin/process_sample.sh" || status=$?
if [[ $status -ne 0 ]]; then
    log "Some isolates failed in stage 1; see samples/<id>/logs. Continuing with the rest."
    overall=1
fi

# ------------------------------------------------------------------------------
# Stage 2: species check with Kraken2/Bracken, one isolate at a time
# ------------------------------------------------------------------------------
if [[ -n "$KRAKEN_DB" ]]; then
    log "Stage 2: Kraken2/Bracken species check, one isolate at a time with $THREADS threads"
    while IFS='|' read -r id platform read1 read2 genome_size; do
        dir="$OUTDIR/samples/$id"
        if [[ -s "$dir/reads.tsv" ]]; then
            IFS=$'\t' read -r platform read1 read2 < "$dir/reads.tsv" || true
        fi
        report="$dir/kraken/$id.kraken.report"
        bracken_out="$dir/kraken/$id.bracken.tsv"
        mkdir -p "$dir/kraken" "$dir/logs"
        if [[ $FORCE -eq 0 && -s "$report" ]]; then
            echo "[$id] kraken2: done earlier"
        elif [[ $DRY_RUN -eq 0 && ! -f "$read1" ]]; then
            echo "[$id] kraken2: reads not found ($read1), skipping" >&2
            overall=1
            continue
        else
            paired=()
            [[ -n "$read2" ]] && paired=(--paired)
            echo "[$id] kraken2: started $(date "+%H:%M:%S")"
            if ! run kraken2 kraken2 --db "$KRAKEN_DB" --threads "$THREADS" --memory-mapping \
                    --report "$report.tmp" --output /dev/null ${paired[@]+"${paired[@]}"} \
                    "$read1" ${read2:+"$read2"} > "$dir/logs/kraken2.log" 2>&1; then
                echo "[$id] kraken2: FAILED, see $dir/logs/kraken2.log" >&2
                overall=1
                continue
            fi
            [[ $DRY_RUN -eq 1 ]] && cat "$dir/logs/kraken2.log" || mv "$report.tmp" "$report"
        fi
        if [[ $FORCE -eq 0 && -s "$bracken_out" ]]; then
            echo "[$id] bracken: done earlier"
        elif run bracken bracken -d "$KRAKEN_DB" -i "$report" -o "$bracken_out.tmp" \
                -w "$dir/kraken/$id.bracken.report" -r "$BRACKEN_READ_LENGTH" -l S \
                > "$dir/logs/bracken.log" 2>&1; then
            [[ $DRY_RUN -eq 1 ]] && cat "$dir/logs/bracken.log" || mv "$bracken_out.tmp" "$bracken_out"
        else
            echo "[$id] bracken: FAILED, see $dir/logs/bracken.log; the Kraken2 report is used instead" >&2
        fi
    done < "$jobs_file"
else
    log "Stage 2: no --kraken-db given, skipping the read-based species check"
fi

# ------------------------------------------------------------------------------
# Stage 3: chewBBACA AlleleCall, one job per schema in parallel
# ------------------------------------------------------------------------------
run_allelecall() {
    local schema="$1"
    local result_dir="$OUTDIR/chewbbaca/$schema/allelecall"
    local cmd=("$APPTAINER" exec $BIND_ARGS "$CONTAINERS_DIR/chewbbaca.sif"
        chewie AlleleCall
        -i "$OUTDIR/chewbbaca/$schema/genomes"
        -g "$SCHEMAS_DIR/$schema/alleles_rereffed"
        -o "$result_dir"
        --cpu "$CPUS_PER_JOB"
        --no-inferred)

    if [[ $FORCE -eq 0 && -n "$(find "$result_dir" -name results_alleles.tsv 2> /dev/null)" ]]; then
        echo "[$schema] results exist, skipping (use --force to re-run)"
        return 0
    fi
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "[$schema] ${cmd[*]}"
        return 0
    fi
    rm -rf "$result_dir"
    echo "[$schema] started $(date "+%H:%M:%S"), log: $OUTDIR/chewbbaca/$schema/allelecall.log"
    if "${cmd[@]}" > "$OUTDIR/chewbbaca/$schema/allelecall.log" 2>&1; then
        echo "[$schema] finished $(date "+%H:%M:%S")"
    else
        echo "[$schema] FAILED, see $OUTDIR/chewbbaca/$schema/allelecall.log" >&2
        return 1
    fi
}

if [[ $SKIP_CHEWBBACA -eq 0 ]]; then
    log "Stage 3: staging assemblies for chewBBACA"
    rm -rf "$OUTDIR"/chewbbaca/*/genomes
    while IFS='|' read -r id platform read1 read2 growth schema genome_size; do
        [[ -n "$schema" ]] || continue
        assembly="$OUTDIR/samples/$id/assembly/$id.fasta"
        if [[ $DRY_RUN -eq 0 && ! -s "$assembly" ]]; then
            echo "  WARNING: no assembly for $id; it is left out of allele calling" >&2
            continue
        fi
        mkdir -p "$OUTDIR/chewbbaca/$schema/genomes"
        ln -sf "$assembly" "$OUTDIR/chewbbaca/$schema/genomes/$id.fasta"
    done < "$SAMPLES"

    schemas=()
    for genomes in "$OUTDIR"/chewbbaca/*/genomes; do
        [[ -d "$genomes" ]] || continue
        schema="$(basename "$(dirname "$genomes")")"
        if [[ ! -d "$SCHEMAS_DIR/$schema/alleles_rereffed" ]]; then
            echo "  WARNING: schema $schema is not set up in $SCHEMAS_DIR (run make ${schema}_all); skipping" >&2
            continue
        fi
        schemas+=("$schema")
    done

    if [[ ${#schemas[@]} -gt 0 ]]; then
        jobs=${#schemas[@]}
        (( jobs > THREADS )) && jobs=$THREADS
        export CPUS_PER_JOB=$(( THREADS / jobs ))
        export SCHEMAS_DIR
        export -f run_allelecall
        log "Stage 3: AlleleCall for ${#schemas[@]} schema(s): ${schemas[*]}; $jobs at a time with $CPUS_PER_JOB thread(s) each"
        status=0
        printf '%s\n' "${schemas[@]}" | xargs -P "$jobs" -I{} bash -c 'run_allelecall "$1"' _ {} || status=$?
        if [[ $status -ne 0 ]]; then
            log "One or more AlleleCall jobs failed; distances are only computed for the ones that finished"
            overall=1
        fi
    else
        log "Stage 3: no schema is ready, skipping allele calling"
    fi
fi

[[ $DRY_RUN -eq 1 ]] && exit 0

# ------------------------------------------------------------------------------
# Stage 4: QC summary and distances within transmission groups
# ------------------------------------------------------------------------------
log "Stage 4: summarising QC"
python3 -I "$REPO_DIR/bin/summarise_qc.py" \
    --reads "$READS" \
    --samplesheet "$SAMPLESHEET" \
    --results "$OUTDIR" \
    --species-map "$SPECIES_MAP" \
    --schemas "$SCHEMA_TABLE" \
    --thresholds "$QC_THRESHOLDS" || overall=1

if [[ $SKIP_CHEWBBACA -eq 0 ]]; then
    log "Stage 4: comparing isolates within transmission groups"
    python3 -I "$REPO_DIR/bin/check_distances.py" \
        --samplesheet "$SAMPLESHEET" \
        --results "$OUTDIR/chewbbaca" \
        --outdir "$OUTDIR" \
        --species-map "$SPECIES_MAP" \
        --schemas "$SCHEMA_TABLE" \
        --qc-summary "$OUTDIR/qc_summary.tsv" || overall=1
fi

exit $overall
