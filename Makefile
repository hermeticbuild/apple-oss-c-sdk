.DEFAULT_GOAL := install
PYTHON ?= python3
MIG ?= /usr/bin/mig

.PHONY: install test
install:
	@set -eu; \
		test -x "$(CLANG)" || { echo "Set CLANG to the pinned LLVM Clang executable." >&2; exit 1; }; \
		test -x "$(MIG)" || { echo "Set MIG to the system MIG executable." >&2; exit 1; }; \
		test -n "$(OUT)" && test ! -e "$(OUT)" || { echo "Set OUT to a new directory." >&2; exit 1; }; \
		stage=$$(mktemp -d "$${TMPDIR:-/tmp}/apple-oss-c-recipes.XXXXXX"); \
		trap 'rm -rf -- "$$stage"' EXIT; \
		$(MAKE) build-install STAGE="$$stage" CLANG="$(CLANG)" MIG="$(MIG)" OUT="$(OUT)"

test:
	@test -x "$(CLANG)" || { echo "Set CLANG to the pinned LLVM Clang executable." >&2; exit 1; }
	@test -n "$(OUT)" && test -f "$(OUT)/header-manifest.tsv" || { echo "Set OUT to the tree produced by make install." >&2; exit 1; }
	$(PYTHON) -m unittest discover -s tests/recipes
	$(PYTHON) -m tools.qualify_headers.compile_probes --clang "$(CLANG)" --sysroot "$(OUT)" \
		--fixture tests/installed_headers/fenv_abi.c \
		--fixture tests/installed_headers/stdatomic_init.c \
		$(if $(filter-out macosx26.5,$(SDK)),,--fixture tests/installed_headers/macos_26_5_availability.c) \
		--fixture tests/installed_headers/complex_abi.c \
		--fixture tests/installed_headers/target_conditionals.c
	$(PYTHON) tests/installed_headers/check_fenv_runtime.py

ifneq ($(strip $(STAGE)),)
# Each copy writes its full receipt as it stages the file.
recipe-path = $(or $(2),recipes/$(1)/Makefile)
define copy-headers
mkdir -p "$(STAGE)/$(1)/dst/usr/include/$(2)"
install -m 644 $(3) "$(STAGE)/$(1)/dst/usr/include/$(2)/"
@for source in $(3); do \
	path="$(if $(filter .,$(2)),usr/include,usr/include/$(2))/$${source##*/}"; \
	printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$$path" "$(1)" "$$source" \
		"$(call recipe-path,$(1),$(4))" copy "$(call recipe-path,$(1),$(4))" "$$source"; \
	done >> "$(STAGE)/$(1)/records"
endef

define record-installed
/bin/sh recipes/record-installed.sh "$(STAGE)/$(1)" "$(1)" "$(2)" "$(3)" "$(4)" $(5) >> "$(STAGE)/$(1)/records"
endef

define header-record
@{ printf '%s\t%s\t%s\t%s\t%s' "$(2)" "$(1)" "$(3)" "$(4)" "$(5)"; \
	for input in $(6); do printf '\t%s' "$$input"; done; printf '\n'; } \
	>> "$(STAGE)/$(1)/records"
endef

.PHONY: stage build-install pre-mig
stage:

include $(wildcard recipes/*/Makefile)

pre-mig: stage
	/bin/sh recipes/merge.sh --bootstrap "$(STAGE)/pre-mig" "$(STAGE)"/*/records

build-install: mig-arm64 mig-x86_64
	diff -rq "$(STAGE)/mig-arm64/dst/usr/include/mach" "$(STAGE)/mig-x86_64/dst/usr/include/mach"
	/bin/sh recipes/merge.sh "$(OUT)" "$(STAGE)"/*/records
endif
