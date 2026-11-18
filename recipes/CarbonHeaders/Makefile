# Compatibility copies. The pinned Makefile puts these in the phone-build CCFILES.
# The standalone macOS probe includes both.
.PHONY: stage-CarbonHeaders
stage: stage-CarbonHeaders
stage-CarbonHeaders: CarbonHeaders
	$(call copy-headers,CarbonHeaders,.,sources/CarbonHeaders/ConditionalMacros.h sources/CarbonHeaders/MacTypes.h)
	$(call record-stage,CarbonHeaders,recipes/CarbonHeaders/Makefile)
