#!/usr/bin/env bash
# Read QC, assembly and assembly QC for one isolate. Called by sinklink.sh with
# the isolate id; its line in $JOBS_FILE is "id|platform|read1|read2|genome_size".
# Settings come from the environment exported by sinklink.sh.
set -euo pipefail

line="$(awk -F'|' -v id="$1" '$1 == id { print; exit }' "$JOBS_FILE")"
[[ -n "$line" ]] || { echo "[$1] not found in $JOBS_FILE" >&2; exit 1; }
IFS='|' read -r id platform read1 read2 genome_size <<< "$line"

dir="$OUTDIR/samples/$id"
logs="$dir/logs"
t=$SAMPLE_THREADS
m=$SAMPLE_MEMORY
mkdir -p "$logs"

run() {
    local sif="$CONTAINERS_DIR/$1.sif"
    shift
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "    $APPTAINER exec$BIND_ARGS $sif $*" >&2
        return 0
    fi
    $APPTAINER exec $BIND_ARGS "$sif" "$@"
}

finish() {
    [[ $DRY_RUN -eq 1 ]] || mv "$1" "$2"
}

step() {
    local name="$1" out="$2" status
    shift 2
    if [[ $FORCE -eq 0 && -s "$out" ]]; then
        echo "[$id] $name: done earlier"
        return 0
    fi
    echo "[$id] $name: started $(date "+%H:%M:%S")"
    if [[ $DRY_RUN -eq 1 ]]; then
        "$@"
        return 0
    fi
    set +e
    ( set -e; "$@" ) > "$logs/$name.log" 2>&1
    status=$?
    set -e
    if [[ $status -eq 0 && -s "$out" ]]; then
        echo "[$id] $name: finished $(date "+%H:%M:%S")"
    else
        echo "[$id] $name: FAILED, see $logs/$name.log" >&2
        return 1
    fi
}

trim_illumina() {
    local d="$dir/trimmomatic"
    mkdir -p "$d"
    if [[ -n "$read2" ]]; then
        run trimmomatic trimmomatic PE -threads "$t" "$read1" "$read2" \
            "$d/${id}_1.tmp.fastq.gz" "$d/${id}_unpaired_1.fastq.gz" \
            "$d/${id}_2.tmp.fastq.gz" "$d/${id}_unpaired_2.fastq.gz" \
            $TRIMMOMATIC_ARGS
        finish "$d/${id}_2.tmp.fastq.gz" "$d/${id}_2.fastq.gz"
    else
        run trimmomatic trimmomatic SE -threads "$t" "$read1" "$d/${id}_1.tmp.fastq.gz" $TRIMMOMATIC_ARGS
    fi
    finish "$d/${id}_1.tmp.fastq.gz" "$d/${id}_1.fastq.gz"
}

filter_nanopore() {
    local d="$dir/filtlong"
    mkdir -p "$d"
    if [[ $DRY_RUN -eq 1 ]]; then
        run filtlong filtlong $FILTLONG_ARGS "$read1"
        return 0
    fi
    run filtlong filtlong $FILTLONG_ARGS "$read1" | gzip -n > "$d/$id.tmp.fastq.gz"
    finish "$d/$id.tmp.fastq.gz" "$d/$id.fastq.gz"
}

fastqc() {
    local d="$dir/fastqc"
    mkdir -p "$d"
    run fastqc fastqc --extract --threads "$t" --outdir "$d" "$read1" ${read2:+"$read2"}
    [[ $DRY_RUN -eq 1 ]] || date > "$d/fastqc.done"
}

nanoplot() {
    local d="$dir/nanoplot"
    run nanoplot NanoPlot --threads "$t" --tsv_stats --prefix "${id}_" --outdir "$d.tmp" --fastq "$read1"
    if [[ $DRY_RUN -eq 0 ]]; then
        rm -rf "$d"
        mv "$d.tmp" "$d"
    fi
}

assemble_skesa() {
    local d="$dir/assembly"
    mkdir -p "$d"
    if [[ $DRY_RUN -eq 1 ]]; then
        run skesa skesa --cores "$t" --memory "$m" --reads "$read1${read2:+,$read2}"
        return 0
    fi
    run skesa skesa --cores "$t" --memory "$m" --reads "$read1${read2:+,$read2}" > "$d/$id.tmp.fasta"
    finish "$d/$id.tmp.fasta" "$d/$id.fasta"
}

assemble_spades() {
    local d="$dir/assembly"
    local input=(-s "$read1")
    [[ -n "$read2" ]] && input=(-1 "$read1" -2 "$read2")
    mkdir -p "$d"
    rm -rf "$d/spades"
    run spades spades.py --isolate "${input[@]}" -t "$t" -m "$m" -o "$d/spades"
    finish "$d/spades/contigs.fasta" "$d/$id.fasta"
}

assemble_flye_medaka() {
    local d="$dir/assembly"
    local size_args=()
    [[ -n "$genome_size" ]] && size_args=(--genome-size "$genome_size" --asm-coverage 50)
    mkdir -p "$d"
    rm -rf "$d/flye" "$d/medaka_round1" "$d/medaka_round2"
    run flye flye --nano-hq "$read1" ${size_args[@]+"${size_args[@]}"} --threads "$t" --out-dir "$d/flye"
    run medaka medaka_consensus -i "$read1" -d "$d/flye/assembly.fasta" -o "$d/medaka_round1" -t "$t" --bacteria
    run medaka medaka_consensus -i "$read1" -d "$d/medaka_round1/consensus.fasta" -o "$d/medaka_round2" -t "$t" --bacteria
    finish "$d/medaka_round2/consensus.fasta" "$d/$id.fasta"
}

quast() {
    local d="$dir/quast"
    rm -rf "$d.tmp"
    run quast quast.py "$assembly" -o "$d.tmp" -t "$t"
    if [[ $DRY_RUN -eq 0 ]]; then
        rm -rf "$d"
        mv "$d.tmp" "$d"
    fi
}

gambitcore() {
    local d="$dir/gambitcore"
    mkdir -p "$d"
    if [[ $DRY_RUN -eq 1 ]]; then
        run gambitcore gambitcore "$GAMBIT_DB" "$assembly"
        return 0
    fi
    run gambitcore gambitcore "$GAMBIT_DB" "$assembly" > "$d/$id.tmp.tsv"
    finish "$d/$id.tmp.tsv" "$d/$id.tsv"
}

map_reads() {
    local d="$dir/mapping"
    mkdir -p "$d"
    if [[ $DRY_RUN -eq 1 ]]; then
        if [[ "$platform" == illumina ]]; then
            run bwakit bwa index -p "$d/$id" "$assembly"
            run bwakit bwa mem -t "$t" "$d/$id" "$read1" ${read2:+"$read2"}
        else
            run minimap2 minimap2 -a -x lr:hq -t "$t" "$assembly" "$read1"
        fi
        run samtools samtools sort -@ "$t" -o "$d/$id.bam" -
        run samtools samtools coverage "$d/$id.bam"
        return 0
    fi
    if [[ "$platform" == illumina ]]; then
        run bwakit bwa index -p "$d/$id" "$assembly"
        run bwakit bwa mem -t "$t" "$d/$id" "$read1" ${read2:+"$read2"} \
            | run samtools samtools sort -@ "$t" -o "$d/$id.bam" -
        rm -f "$d/$id".{amb,ann,bwt,pac,sa}
    else
        run minimap2 minimap2 -a -x lr:hq -t "$t" "$assembly" "$read1" \
            | run samtools samtools sort -@ "$t" -o "$d/$id.bam" -
    fi
    run samtools samtools index "$d/$id.bam"
    run samtools samtools coverage "$d/$id.bam" > "$d/$id.coverage.tmp.tsv"
    finish "$d/$id.coverage.tmp.tsv" "$d/$id.coverage.tsv"
}

mlst() {
    local d="$dir/mlst"
    mkdir -p "$d"
    if [[ $DRY_RUN -eq 1 ]]; then
        run mlst mlst --json "$d/$id.json" --threads "$t" "$assembly"
        return 0
    fi
    run mlst mlst --json "$d/$id.json" --threads "$t" "$assembly" > "$d/$id.tmp.tsv"
    finish "$d/$id.tmp.tsv" "$d/$id.tsv"
}

if [[ "$platform" == illumina ]]; then
    if [[ $TRIM -eq 1 ]]; then
        step trimmomatic "$dir/trimmomatic/${id}_1.fastq.gz" trim_illumina
        read1="$dir/trimmomatic/${id}_1.fastq.gz"
        [[ -n "$read2" ]] && read2="$dir/trimmomatic/${id}_2.fastq.gz"
    fi
    step fastqc "$dir/fastqc/fastqc.done" fastqc
    step "$ASSEMBLER" "$dir/assembly/$id.fasta" "assemble_$ASSEMBLER"
else
    if [[ $FILTLONG -eq 1 ]]; then
        step filtlong "$dir/filtlong/$id.fastq.gz" filter_nanopore
        read1="$dir/filtlong/$id.fastq.gz"
    fi
    step nanoplot "$dir/nanoplot/${id}_NanoStats.txt" nanoplot
    step flye_medaka "$dir/assembly/$id.fasta" assemble_flye_medaka
fi

printf '%s\t%s\t%s\n' "$platform" "$read1" "$read2" > "$dir/reads.tsv"

assembly="$dir/assembly/$id.fasta"
status=0
step quast "$dir/quast/transposed_report.tsv" quast || status=1
if [[ -n "$GAMBIT_DB" ]]; then
    step gambitcore "$dir/gambitcore/$id.tsv" gambitcore || status=1
fi
step mapping "$dir/mapping/$id.coverage.tsv" map_reads || status=1
step mlst "$dir/mlst/$id.tsv" mlst || status=1
exit $status
