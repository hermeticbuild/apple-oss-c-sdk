#!/bin/sh
# Seal one producer's public staged headers. Optional overrides describe
# individual outputs that were generated or transformed by that producer.
set -eu
stage=$1
owner=$2
rule=$3
shift 3
include="$stage/dst/usr/include"
touch "$stage/direct-copies" "$stage/overrides"
find "$include" -name '*.h' \( -type f -o -type l \) -print > "$stage/paths"
test -s "$stage/paths" || { echo "$owner staged no public headers" >&2; exit 1; }
printf '%s\n' "$@" > "$stage/inputs"

awk -v FS='\t' -v OFS='\t' -v prefix="$include/" -v owner="$owner" -v rule="$rule" '
    FILENAME == ARGV[1] {
        sub(/^\.\//, "", $1)
        if (copies[$1]++) { print "duplicate copy:", $1 > "/dev/stderr"; exit 1 }
        sources[$1] = $2
        next
    }
    FILENAME == ARGV[2] {
        if (overrides[$1]++) { print "duplicate override:", $1 > "/dev/stderr"; exit 1 }
        records[$1] = $0
        next
    }
    FILENAME == ARGV[3] { if (length($0)) deps = deps OFS $0; next }
    {
        relative = substr($0, length(prefix) + 1)
        path = "usr/include/" relative
        if (path in records) {
            print records[path]
            delete records[path]
        } else if (relative in sources) {
            print path, owner, sources[relative], rule, "copy", rule OFS sources[relative]
        } else {
            transform = rule ~ /^sources\// ? "Apple public header install" : "producer header install recipe"
            print path, owner, "staged:" owner ":" relative, rule, transform, rule deps
        }
        delete sources[relative]
    }
    END {
        for (file in sources) { print "missing copied header:", file > "/dev/stderr"; exit 1 }
        for (file in records) { print "missing overridden header:", file > "/dev/stderr"; exit 1 }
    }
' "$stage/direct-copies" "$stage/overrides" "$stage/inputs" "$stage/paths" > "$stage/records"
