# mosdepth quantized regions below the depth cut-off, plus the reference's repeat and prophage mask.
FILENAME ~ /quantized/ {
    if ($4 == "LOW") print $1 "\t" $2 "\t" $3
    next
}
{ print }
