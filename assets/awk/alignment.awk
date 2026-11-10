# Join the pseudogenomes and the reference chromosome (-v ref=<file>), naming the latter Reference.
FNR == 1 && FILENAME == ref { print ">Reference"; next }
{ print }
