# Read pinned Git objects directly. A working checkout or a bare repo works.
define prepare-source
@set -eu; \
	repo="$(SOURCE_ROOT)/$(1)"; \
	if test ! -e "$$repo"; then \
		mkdir -p "$(SOURCE_ROOT)"; \
		temp=$$(mktemp -d "$(SOURCE_ROOT)/.fetch-$(1).XXXXXX"); \
		trap 'rm -rf -- "$$temp"' EXIT; \
		git init --quiet --bare "$$temp"; \
		git -C "$$temp" fetch --quiet --depth=1 --no-tags \
			"https://github.com/apple-oss-distributions/$(1).git" "$(2)"; \
		git -C "$$temp" cat-file -e "$(2)^{commit}"; \
		mv "$$temp" "$$repo"; \
	else \
		git -C "$$repo" cat-file -e "$(2)^{commit}"; \
	fi
endef

# Emit only the format shared by the small C framework stubs.
define write-tbd
@set -eu; \
	targets='[ arm64-macos, x86_64-macos ]'; \
	{ \
		printf '%s\n' '--- !tapi-tbd' 'tbd-version: 4' "targets: $$targets" \
			"install-name: '/System/Library/Frameworks/$(1).framework/$(1)'"; \
		if test -n "$(2)"; then \
			symbols=$$(LC_ALL=C sort -u "$(2)"); \
			test -n "$$symbols"; \
			printf 'exports:\n  - targets: %s\n    symbols: [' "$$targets"; \
			separator=' '; \
			for symbol in $$symbols; do \
				printf "%s'_%s'" "$$separator" "$$symbol"; \
				separator=', '; \
			done; \
			printf ' ]\n'; \
		fi; \
		printf '%s\n' '...'; \
	} > "$(STAGE)/$(1).framework/$(1).tbd"
endef

define stage-local-framework
	mkdir -p "$(STAGE)/$(1).framework/Headers" "$(STAGE)/$(1).framework/Modules"
	install -m 644 $(1)/Headers/*.h "$(STAGE)/$(1).framework/Headers/"
	printf 'framework module %s [system] {\n  umbrella header "%s.h"\n  export *\n  module * { export * }\n}\n' \
		'$(1)' '$(1)' > "$(STAGE)/$(1).framework/Modules/module.modulemap"
	$(call write-tbd,$(1),$(2))
endef

# Protect the source and the final output from direct staging invocations.
.PHONY: require-stage
require-stage:
	@test -n "$(STAGE)" && test -d "$(STAGE)" || { echo "Run make install to stage frameworks." >&2; exit 1; }

test-clang = "$(CLANG)" --no-default-config -target "$$cpu-apple-macos14.0" -isysroot "$(SDK)" \
	-nostdinc -isystem "$$resource/include" -isystem "$(SDK)/usr/include" \
	-F "$(SDK)/System/Library/Frameworks" -std=c11 -Werror

define test-framework-link
@set -eu; \
	work=$$(mktemp -d "$${TMPDIR:-/tmp}/framework-tests.XXXXXX"); \
	trap 'rm -rf -- "$$work"' EXIT; \
	resource=$$("$(CLANG)" --no-default-config -print-resource-dir); \
	for cpu in arm64 x86_64; do \
		$(test-clang) $(2) -fuse-ld=lld -nostdlib "$(1)/test.c" \
			-framework "$(1)" -lSystem -o "$$work/test-$$cpu"; \
		if test "$(RUN)" = 1; then "$$work/test-$$cpu"; fi; \
		echo "$$cpu $(1) link probe passed"; \
	done
endef

define test-framework-headers
@set -eu; \
	resource=$$("$(CLANG)" --no-default-config -print-resource-dir); \
	for cpu in arm64 x86_64; do \
		$(test-clang) -fsyntax-only "$(1)/test.c"; \
		echo "$$cpu $(1) header probe passed"; \
	done
endef
