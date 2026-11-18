# First input: shasum output. Second input: sorted stage records.
BEGIN {
    FS = "\t"
    print "{\n  \"schema\": 1,\n  \"files\": {" > owners
    print "{\n  \"schema\": 2,\n  \"files\": {" > provenance
}
function quote(value,    i, c, result) {
    result = "\""
    for (i = 1; i <= length(value); i++) {
        c = substr(value, i, 1)
        if (c == "\"" || c == "\\") c = "\\" c
        result = result c
    }
    return result "\""
}
FNR == NR { split($0, fields, / +/); hash[fields[2]] = fields[1]; next }
{
    if (!($2 in hash)) { print "missing hash for " $2 > "/dev/stderr"; failed = 1; exit 1 }
    if (count++) {
        print "," > owners
        print "," > provenance
    }
    path = quote($2)
    common = "\"origin\": " quote($4) ", \"selection\": " quote($5)
    printf "    %s: {\"owner\": %s, %s, \"transform\": %s, \"inputs\": [", \
        path, quote($3), common, quote($6) > owners
    for (i = 7; i <= NF; i++) printf "%s%s", (i == 7 ? "" : ", "), quote($i) > owners
    printf "]}" > owners
    printf "    %s: {%s, \"sha256\": %s}", path, common, quote(hash[$2]) > provenance
}
END {
    if (failed || !count) exit 1
    print "\n  }\n}" > owners
    print "\n  }\n}" > provenance
}
