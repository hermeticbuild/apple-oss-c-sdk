CF_COMMIT := dc54c6bb1c1e5e0b9486c1d26dd5bef110b20bf3
CF_STUB := System/Library/Frameworks/CoreFoundation.framework/CoreFoundation.tbd
CF_STUB_INPUT_SHA256 := 2762fd6c1d1ca0b834460550df1b08bb6cf2218cf74525f443e7029861246fa1
CF_STUB_OUTPUT_SHA256 := af6c182cb111f52124b56c037390acbe8a5b78f071c675507b6a035d8969b56c

.PHONY: prepare-CF
prepare-CF:
	$(call prepare-source,CF,$(CF_COMMIT))

CoreFoundation: require-stage
	@test -n "$(SDK_GEN)" || { echo "Set SDK_GEN to the extracted Apple SDK Gen 0.0.4 macOS SDK." >&2; exit 1; }
	@set -eu; \
		input="$(SDK_GEN)/$(CF_STUB)"; \
		staged="$(STAGE)/CoreFoundation.framework"; \
		printf '%s  %s\n' "$(CF_STUB_INPUT_SHA256)" "$$input" | shasum -a 256 -c -; \
		mkdir -p "$$staged/Headers"; \
		while IFS= read -r header; do \
			git -C "$(SOURCE_ROOT)/CF" show "$(CF_COMMIT):$$header" > "$$staged/Headers/$$header"; \
		done < CoreFoundation/headers.list; \
		sed 's/^    symbols:      \[ /&_CFRelease, ___CFConstantStringClassReference, /' \
			"$$input" > "$$staged/CoreFoundation.tbd"; \
		printf '%s  %s\n' "$(CF_STUB_OUTPUT_SHA256)" "$$staged/CoreFoundation.tbd" | shasum -a 256 -c -

test-CoreFoundation:
	$(call test-framework-link,CoreFoundation)
