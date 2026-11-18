.DEFAULT_GOAL := install
PYTHON ?= python3
MIG ?= /usr/bin/mig

.PHONY: install
install:
	@set -eu; \
		test -x "$(CLANG)" || { echo "Set CLANG to the pinned LLVM Clang executable." >&2; exit 1; }; \
		test -x "$(MIG)" || { echo "Set MIG to the system MIG executable." >&2; exit 1; }; \
		test -n "$(OUT)" && test ! -e "$(OUT)" || { echo "Set OUT to a new directory." >&2; exit 1; }; \
		stage=$$(mktemp -d "$${TMPDIR:-/tmp}/apple-oss-c-recipes.XXXXXX"); \
		trap 'rm -rf -- "$$stage"' EXIT; \
		$(MAKE) build-install STAGE="$$stage" CLANG="$(CLANG)" MIG="$(MIG)" OUT="$(OUT)"

ifneq ($(strip $(STAGE)),)
# Producer recipes install into separate roots. A receipt identifies each
# root's recipe to the common assembler.
define copy-headers
mkdir -p "$(STAGE)/$(1)/dst/usr/include/$(2)"
install -m 644 $(3) "$(STAGE)/$(1)/dst/usr/include/$(2)/"
@for source in $(3); do printf '%s\t%s\n' "$(2)/$${source##*/}" "$$source"; done \
	>> "$(STAGE)/$(1)/direct-copies"
endef

define record-stage
printf '%s\n' "$(2)" > "$(STAGE)/$(1)/rule"
endef

include recipes/upstream.mk
include recipes/xnu/Makefile recipes/copyfile/Makefile recipes/zlib/Makefile recipes/libiconv/Makefile
include recipes/hfs/Makefile recipes/CommonCrypto/Makefile recipes/libmalloc/Makefile recipes/libm/Makefile
include recipes/CarbonHeaders/Makefile recipes/libunwind/Makefile recipes/libplatform/Makefile
include recipes/libpthread/Makefile recipes/libdispatch/Makefile recipes/cctools/Makefile recipes/dyld/Makefile

.PHONY: build-install pre-mig
pre-mig: stage
	"$(PYTHON)" -m recipes.build pre-mig "$(STAGE)" "$(STAGE)/pre-mig"

build-install: mig-arm64 mig-x86_64
	diff -rq "$(STAGE)/mig-arm64/mach" "$(STAGE)/mig-x86_64/mach"
	"$(PYTHON)" -m recipes.build assemble "$(STAGE)" "$(OUT)"
endif
