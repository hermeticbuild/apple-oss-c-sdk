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
# Producer recipes seal their own staging directories before the merge.
define copy-headers
mkdir -p "$(STAGE)/$(1)/dst/usr/include/$(2)"
install -m 644 $(3) "$(STAGE)/$(1)/dst/usr/include/$(2)/"
@for source in $(3); do printf '%s\t%s\n' "$(2)/$${source##*/}" "$$source"; done \
	>> "$(STAGE)/$(1)/direct-copies"
endef

define record-stage
/bin/sh recipes/stage.sh "$(STAGE)/$(1)" "$(1)" "$(2)" $(3)
endef

define header-override
@{ printf '%s\t%s\t%s\t%s\t%s' "$(2)" "$(1)" "$(3)" "$(4)" "$(5)"; \
	for input in $(6); do printf '\t%s' "$$input"; done; printf '\n'; } \
	>> "$(STAGE)/$(1)/overrides"
endef

.PHONY: stage build-install pre-mig
stage:

include $(wildcard recipes/*/Makefile)

pre-mig: stage
	/bin/sh recipes/merge.sh "$(STAGE)/pre-mig" "$(STAGE)"/*/records

build-install: mig-arm64 mig-x86_64
	diff -rq "$(STAGE)/mig-arm64/dst/usr/include/mach" "$(STAGE)/mig-x86_64/dst/usr/include/mach"
	/bin/sh recipes/merge.sh "$(OUT)" "$(STAGE)"/*/records
endif
