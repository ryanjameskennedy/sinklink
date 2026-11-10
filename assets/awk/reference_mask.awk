# Repeats: hits of a nucmer self-alignment (show-coords -r) other than each region's match to itself.
# Prophages: PhiSpy prophage coordinates (number, contig, start, stop, ...).
# Prints one BED line per region on the reference contigs.
FILENAME ~ /\.coords$/ && $1 ~ /^[0-9]+$/ && $3 == "|" {
    if ($12 == $13 && $1 == $4 && $2 == $5) next
    start = $4 < $5 ? $4 : $5
    end = $4 < $5 ? $5 : $4
    print $13 "\t" start - 1 "\t" end
    next
}
FILENAME ~ /\.tsv$/ && $3 ~ /^[0-9]+$/ {
    print $2 "\t" $3 - 1 "\t" $4
}
