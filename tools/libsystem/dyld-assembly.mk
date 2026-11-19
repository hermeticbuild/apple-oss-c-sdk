ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
SOURCE_DIGESTS := $(ROOT)/tools/libsystem/data/macosx26.5/dyld-assembly.sha256
PYTHON ?= python3

.PHONY: dyld-assembly dyld-assembly-inputs dyld-assembly-arm64 dyld-assembly-x86_64
dyld-assembly: dyld-assembly-arm64 dyld-assembly-x86_64

dyld-assembly-inputs:
	@test -n "$(WORK)" && test -n "$(SOURCE_ROOT)" && test -n "$(LLVM)" && test -f "$(C_INSTALL)/header-manifest.tsv" || { \
		echo "Set WORK, SOURCE_ROOT, LLVM and C_INSTALL" >&2; exit 2; }
	llvm=$$(cd "$(LLVM)" && pwd -P) && cd "$(ROOT)" && \
		$(PYTHON) -c 'from pathlib import Path; import sys; from tools.toolchain.official_llvm import PIN, projection, read_lock; projection(Path(sys.argv[1]), read_lock(PIN))' "$$llvm"
	cd "$(SOURCE_ROOT)" && shasum -a 256 -c "$(SOURCE_DIGESTS)"
	@set -eu; cd "$(C_INSTALL)"; \
		awk -F '\t' '$$1 == "usr/include/TargetConditionals.h" { record = $$2 "  " $$1; found++ } END { if (found == 1) print record }' \
			header-manifest.tsv | shasum -a 256 -c -
	@mkdir -p "$(WORK)"

dyld-assembly-arm64 dyld-assembly-x86_64: dyld-assembly-%: dyld-assembly-inputs
	@set -eu; \
		sources=$$(cd "$(SOURCE_ROOT)" && pwd -P); \
		scratch=$$(mktemp -d "$(WORK)/.dyld-assembly-$*.XXXXXX"); \
		cleanup() { \
			for name in System helpers.o nm.txt helpers.symbols; do \
				if test -e "$$scratch/$$name" || test -L "$$scratch/$$name"; then unlink "$$scratch/$$name"; fi; \
			done; \
			rmdir "$$scratch"; \
		}; \
		trap cleanup EXIT; \
		ln -s "$$sources/xnu/osfmk" "$$scratch/System"; \
		env -i PATH=/usr/bin:/bin LC_ALL=C "$(LLVM)/bin/clang" \
			-x assembler-with-cpp --no-default-config -target "$*-apple-macos11.0" \
			-isysroot "$(C_INSTALL)" -nostdinc -I"$$scratch" -I"$$sources/xnu/osfmk" -I"$(C_INSTALL)/usr/include" \
			-DPRIVATE=1 -DTARGET_OS_EXCLAVEKIT=0 \
			-c "$$sources/dyld/libdyld/threadLocalHelpers.s" -o "$$scratch/helpers.o"; \
		"$(LLVM)/bin/llvm-lipo" "$$scratch/helpers.o" -verify_arch "$*"; \
		"$(LLVM)/bin/llvm-nm" -m "$$scratch/helpers.o" > "$$scratch/nm.txt"; \
		awk '$$2 == "(__TEXT,__text)" && $$3 == "external" && ($$4 == "__tlv_bootstrap" || $$4 == "dyld_stub_binder") { print $$4 }' \
			"$$scratch/nm.txt" | LC_ALL=C sort > "$$scratch/helpers.symbols"; \
		printf '%s\n' __tlv_bootstrap dyld_stub_binder | diff - "$$scratch/helpers.symbols"; \
		mv "$$scratch/helpers.o" "$(WORK)/dyld-thread-local-helpers-$*.o"; \
		mv "$$scratch/helpers.symbols" "$(WORK)/dyld-thread-local-helpers-$*.symbols"
