# Share of each sequence in an alignment that is N or a gap, as Gubbins counts it.
BEGIN { OFS = "\t"; print "sequence", "missing_percent" }
/^>/ { report(); id = substr($1, 2); bases = 0; missing = 0; next }
{ bases += length($0); missing += gsub(/[Nn-]/, "") }
END { report() }
function report() {
    if (id != "") print id, sprintf("%.2f", bases ? 100 * missing / bases : 100)
}
