#!/bin/sh
# Public macOS Libsyscall MIG headers. Follow mach_install_mig.sh's MIGS list
# and use its attribute filter after preprocessing with the pinned Clang.
set -eu

case "$1" in
    arm64) machine=armv7 ;;
    x86_64) machine=i386 ;;
    *) echo "unsupported MIG target: $1" >&2; exit 1 ;;
esac
mig=$2
clang=$3
sysroot=$4
test -d "$sysroot/usr/include" || { echo "MIG sysroot missing: $sysroot" >&2; exit 1; }
stage=$5
out="$stage/dst/usr/include"
xnu="$PWD/sources/xnu"
libsyscall="$xnu/libsyscall"
script="$libsyscall/xcodescripts/mach_install_mig.sh"

names=$(awk '
    /^MIGS="/ { sub(/^MIGS="/, ""); reading=1 }
    reading {
        last = sub(/"$/, "")
        for (i = 1; i <= NF; i++) {
            if ($i !~ /^[[:alnum:]_]+\.defs$/ || seen[$i]++) exit 1
            print $i
            count++
        }
        if (last) { reading=0; complete=1 }
    }
    /MIGS="\$MIGS mach_vm\.defs"/ { vm=1 }
    END { if (!complete || !count || !vm || seen["mach_vm.defs"]) exit 1 }
' "$script")
test ! -e "$stage"
mkdir -p "$out/mach"
for defs in $names mach_vm.defs; do
    header="$out/mach/${defs%.defs}.h"
    "$mig" -cc "$clang" -novouchers -arch "$machine" -isysroot "$sysroot" \
        "-I$xnu/osfmk" -DLIBSYSCALL_INTERFACE -user /dev/null -server /dev/null \
        -header "$header" "$libsyscall/mach/$defs"
    awk -f "$libsyscall/xcodescripts/filter_mig.awk" \
        "$libsyscall/mach/add_attributes_to_mig.txt" "$header" > "$header.filtered"
    mv "$header.filtered" "$header"
    # The x86_64 stage is only used for the comparison in Make.
    if [ "$1" = arm64 ]; then
        name=$(basename "$header")
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            "usr/include/mach/$name" xnu "generated:system-mig:$name via recipes/xnu/mig.sh" \
            "xnu/libsyscall/xcodescripts/mach_install_mig.sh:public" \
            "system MIG for arm64 and x86_64, then filter" recipes/xnu/mig.sh \
            "sources/xnu/libsyscall/mach/$defs" \
            sources/xnu/libsyscall/xcodescripts/filter_mig.awk \
            sources/xnu/libsyscall/mach/add_attributes_to_mig.txt \
            sources/xnu/libsyscall/xcodescripts/mach_install_mig.sh >> "$stage/records"
    fi

done
