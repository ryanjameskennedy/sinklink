# Keep the chromosome (the first record) and name it after the sample (-v id=...).
/^>/ { n++; if (n == 1) print ">" id; next }
n == 1
