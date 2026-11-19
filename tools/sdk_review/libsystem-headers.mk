# Run from the repository root after make install and make test.
PYTHON ?= python3
MINIMUM ?= 11.0
SDK ?= macosx26.5
CLANG = $(LLVM)/bin/clang
BASELINE = $(wildcard tools/sdk_review/inventories/$(SDK).json)
ROOTS = tools/qualify_headers/fixtures/default_profile.c
DISCOVERY = tools/qualify_headers/fixtures/sdk_discovery.c

.PHONY: header-backlog census paths discovery semantics inputs
inputs:
	@test -x "$(CLANG)" && test -f "$(C_INSTALL)/header-manifest.tsv" && test -f "$(APPLE_SDK)/SDKSettings.json" || { echo "Set LLVM, C_INSTALL and APPLE_SDK" >&2; exit 2; }
	@test -n "$(WORK)" || { echo "Set WORK to a local report directory" >&2; exit 2; }
	@test "$$("/usr/bin/plutil" -extract CanonicalName raw -o - "$(APPLE_SDK)/SDKSettings.json")" = "$(SDK)" || { echo "SDK must match the reference SDK's CanonicalName" >&2; exit 2; }
	@mkdir -p "$(WORK)"

census: inputs
	$(PYTHON) -m tools.qualify_headers.census --clang "$(CLANG)" --c-install "$(C_INSTALL)" --minimum "$(MINIMUM)" --out "$(WORK)/census.json" --report-only

paths: inputs
	$(PYTHON) -m tools.qualify_headers.trace_includes --probe "$(ROOTS)" --clang "$(CLANG)" --sysroot "$(C_INSTALL)" --out "$(WORK)/generated.json"
	$(PYTHON) -m tools.qualify_headers.trace_includes --probe "$(ROOTS)" --clang "$(CLANG)" --sysroot "$(APPLE_SDK)" --out "$(WORK)/reference.json"
	$(PYTHON) -m tools.sdk_review.audit_sdk_headers --sdk "$(APPLE_SDK)" --installation "$(C_INSTALL)" --clang "$(CLANG)" --reference "$(WORK)/reference.json" --generated-probe "$(WORK)/generated.json" $(if $(BASELINE),--baseline "$(BASELINE)") --out "$(WORK)/header-audit.json" --review-out "$(WORK)/header-review.md"

semantics: inputs
	$(PYTHON) -m tools.sdk_review.compare_c_interfaces --clang "$(CLANG)" --installation "$(C_INSTALL)" --sdk "$(APPLE_SDK)" --out "$(WORK)/semantics.json"

discovery: inputs
	$(PYTHON) -m tools.qualify_headers.trace_includes --report-only --probe "$(DISCOVERY)" --clang "$(CLANG)" --sysroot "$(C_INSTALL)" --out "$(WORK)/discovery-generated.json"
	$(PYTHON) -m tools.qualify_headers.trace_includes --report-only --probe "$(DISCOVERY)" --clang "$(CLANG)" --sysroot "$(APPLE_SDK)" --out "$(WORK)/discovery-reference.json"

header-backlog: census paths semantics discovery
	$(PYTHON) -m tools.sdk_review.header_backlog --c-install "$(C_INSTALL)" --census "$(WORK)/census.json" --sdk-audit "$(WORK)/header-audit.json" --semantic "$(WORK)/semantics.json" --reference-sdk "$(APPLE_SDK)" --clang "$(CLANG)" --out "$(WORK)/header-backlog.json"
