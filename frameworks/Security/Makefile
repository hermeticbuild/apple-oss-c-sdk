SECURITY_COMMIT := 97c3a4296c1ea06b0fe1877a7e616aa84450b5b2

.PHONY: prepare-Security
prepare-Security:
	$(call prepare-source,Security,$(SECURITY_COMMIT))

Security: require-stage
	@set -eu; \
		headers="$(STAGE)/Security.framework/Headers"; \
		mkdir -p "$$headers"; \
		while IFS= read -r source; do \
			git -C "$(SOURCE_ROOT)/Security" show "$(SECURITY_COMMIT):$$source" > "$$headers/$${source##*/}"; \
		done < Security/headers.list

test-Security:
	$(call test-framework-headers,Security)
