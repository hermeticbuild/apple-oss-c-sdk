#!/bin/sh
# Merge sealed producer stages. No producer-specific rules belong here.
set -eu
export LC_ALL=C
out=$1
shift
test ! -e "$out" && test ! -L "$out" || { echo "output already exists: $out" >&2; exit 1; }
parent=$(dirname "$out")
mkdir -p "$parent"
scratch=$(mktemp -d "$parent/.apple-headers.XXXXXX")
trap 'rm -rf -- "$scratch"' EXIT
tree="$scratch/tree"
mkdir "$tree"

# Keep the originating stage next to each row, and sort by installed path.
for records do
    test -s "$records" || { echo "empty stage: $records" >&2; exit 1; }
    include=$(realpath "$(dirname "$records")/dst/usr/include")
    awk -v include="$include" '{ print include "\t" $0 }' "$records"
done > "$scratch/unsorted"
tab=$(printf '\t')
sort -t "$tab" -k2,2 "$scratch/unsorted" > "$scratch/records"
awk -F '\t' '
    NF < 7 || $2 !~ /^usr\/include\/[[:alnum:]_.+\/-]+\.h$/ || $2 ~ /(^|\/)\.\.?($|\/)|\/\// {
        print "invalid header record:", $0 > "/dev/stderr"; exit 1
    }
    {
        for (i = 1; i <= NF; i++) {
            if ($i == "" || $i ~ /[[:cntrl:]]/) {
                print "empty or invalid field for:", $2 > "/dev/stderr"; exit 1
            }
        }
    }
    $2 == previous {
        print "multiple owners for " $2 ": " owner ", " $3 > "/dev/stderr"; exit 1
    }
    { previous=$2; owner=$3 }
    END { if (!NR) exit 1 }
' "$scratch/records"

while IFS="$tab" read -r include path owner origin selection transform inputs; do
    source=$(realpath "$include/${path#usr/include/}")
    case "$source" in "$include"/*) ;; *) echo "header escapes stage: $path" >&2; exit 1 ;; esac
    test -f "$source"
    # The validated input fields are tab-separated. Turn off glob expansion
    # while splitting them, so source paths with spaces remain single inputs.
    IFS="$tab"
    set -f
    for input in $inputs; do
        case "$input" in
            */../*|*/..|*/./*|*/.) echo "invalid producer input: $input" >&2; exit 1 ;;
            sources/*|recipes/*) test -f "$input" || { echo "missing producer input: $input" >&2; exit 1; } ;;
            *) echo "invalid producer input: $input" >&2; exit 1 ;;
        esac
    done
    set +f
    unset IFS
    directory="$tree/${path%/*}"
    test -d "$directory" || mkdir -p "$directory"
    install -m 0644 "$source" "$tree/$path"
done < "$scratch/records"

(cd "$tree" && find usr/include -type f -exec shasum -a 256 {} +) > "$scratch/hashes"
awk -v owners="$tree/header-owners.json" -v provenance="$tree/header-provenance.json" \
    -f recipes/manifests.awk "$scratch/hashes" "$scratch/records"
mv "$tree" "$out"
