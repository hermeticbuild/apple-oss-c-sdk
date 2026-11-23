SECURITY_COMMIT := 97c3a4296c1ea06b0fe1877a7e616aa84450b5b2

.PHONY: prepare-Security
prepare-Security:
	$(call prepare-source,Security,$(SECURITY_COMMIT))

Security: require-stage
	mkdir -p "$(STAGE)/Security.framework/Headers"
	git -C "$(SOURCE_ROOT)/Security" show "$(SECURITY_COMMIT):OSX/libsecurity_authorization/lib/Authorization.h" \
		> "$(STAGE)/Security.framework/Headers/Authorization.h"

test-Security:
	$(call test-framework-headers,Security)
