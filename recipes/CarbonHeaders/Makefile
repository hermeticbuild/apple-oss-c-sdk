# The probe needs the two compatibility copies from the phone-build CCFILES.
carbon_root = $(STAGE)/CarbonHeaders/dst
carbon_include = $(carbon_root)/usr/include
carbon_template = sources/CarbonHeaders/TargetConditionals.h

.PHONY: stage-CarbonHeaders
stage: stage-CarbonHeaders
stage-CarbonHeaders:
	mkdir -p "$(carbon_root)"
	env -i PATH="$$PATH" $(MAKE) -C sources/CarbonHeaders installhdrs \
		DSTROOT="$(carbon_root)" RC_ARCHS="arm64 x86_64"
	@# AvailabilityVersions supplies these public headers.
	rm "$(carbon_include)/Availability.h" "$(carbon_include)/AvailabilityInternal.h" \
		"$(carbon_include)/AvailabilityMacros.h"
	$(call copy-headers,CarbonHeaders,.,sources/CarbonHeaders/ConditionalMacros.h sources/CarbonHeaders/MacTypes.h)
	"$(PYTHON)" recipes/CarbonHeaders/target_conditionals.py "$(carbon_include)/TargetConditionals.h"
	$(call header-override,CarbonHeaders,usr/include/TargetConditionals.h,derived:$(carbon_template) via recipes/CarbonHeaders/target_conditionals.py,CarbonHeaders derivation,resolve macOS placeholders and derive arm64 aliases,$(carbon_template))
	$(call record-stage,CarbonHeaders,recipes/CarbonHeaders/Makefile)
