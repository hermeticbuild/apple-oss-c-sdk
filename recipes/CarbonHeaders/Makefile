# The probe needs the two compatibility copies from the phone-build CCFILES.
carbon_root = $(STAGE)/CarbonHeaders/dst
carbon_include = $(carbon_root)/usr/include
carbon_template = sources/CarbonHeaders/TargetConditionals.h

.PHONY: stage-CarbonHeaders
stage: stage-CarbonHeaders
stage-CarbonHeaders:
	mkdir -p "$(carbon_root)"
	env -i PATH="$$PATH" $(MAKE) -C "$(SOURCE_ROOT)/CarbonHeaders" installhdrs \
		DSTROOT="$(carbon_root)" RC_ARCHS="arm64 x86_64"
	@# AvailabilityVersions supplies these public headers.
	rm "$(carbon_include)/Availability.h" "$(carbon_include)/AvailabilityInternal.h" \
		"$(carbon_include)/AvailabilityMacros.h"
ifeq ($(SDK),macosx26.5)
	$(call copy-headers,CarbonHeaders,.,sources/CarbonHeaders/ConditionalMacros.h)
	"$(PYTHON)" recipes/CarbonHeaders/macos_26_5.py "$(SOURCE_ROOT)/CarbonHeaders/MacTypes.h" "$(carbon_include)"
	$(call header-record,CarbonHeaders,usr/include/AssertMacros.h,derived:sources/CarbonHeaders/AssertMacros.h,recipes/CarbonHeaders/macos_26_5.py,default short names off while retaining explicit opt-in,sources/CarbonHeaders/AssertMacros.h sources/CarbonHeaders/Makefile recipes/CarbonHeaders/macos_26_5.py)
	$(call header-record,CarbonHeaders,usr/include/MacTypes.h,derived:sources/CarbonHeaders/MacTypes.h,recipes/CarbonHeaders/macos_26_5.py,prototype the two no-argument callbacks,sources/CarbonHeaders/MacTypes.h recipes/CarbonHeaders/macos_26_5.py)
else
	$(call copy-headers,CarbonHeaders,.,sources/CarbonHeaders/ConditionalMacros.h sources/CarbonHeaders/MacTypes.h)
	$(call record-installed,CarbonHeaders,recipes/CarbonHeaders/Makefile,usr/include/AssertMacros.h)
endif
	"$(PYTHON)" recipes/CarbonHeaders/target_conditionals.py "$(carbon_include)/TargetConditionals.h"
	$(call header-record,CarbonHeaders,usr/include/TargetConditionals.h,derived:$(carbon_template) via recipes/CarbonHeaders/target_conditionals.py,CarbonHeaders derivation,resolve macOS placeholders and derive architecture and ABI aliases,$(carbon_template) recipes/CarbonHeaders/target_conditionals.py recipes/CarbonHeaders/macos-abi.md)
