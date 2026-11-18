# Each Apple project installs into a fresh private staging directory.
CMAKE ?= cmake
NINJA ?= ninja
ARCHS := arm64 x86_64

ifeq ($(strip $(STAGE)),)
$(error STAGE must name a fresh staging directory)
endif

.PHONY: stage architecture CarbonHeaders Libinfo Libc AvailabilityVersions
stage: architecture CarbonHeaders Libinfo Libc AvailabilityVersions

architecture CarbonHeaders:
	mkdir -p "$(STAGE)/$@/dst"
	env -i PATH="$$PATH" $(MAKE) -C "sources/$@" installhdrs \
		DSTROOT="$(STAGE)/$@/dst" RC_ARCHS="$(ARCHS)"

Libinfo:
	mkdir -p "$(STAGE)/$@/dst"
	cd sources/$@ && env -i PATH="$$PATH" DSTROOT="$(STAGE)/$@/dst" \
		PLATFORM_NAME=macosx ACTION=installhdrs \
		INSTALL_OWNER="$$(id -un)" INSTALL_GROUP="$$(id -gn)" \
		/bin/bash -e xcodescripts/install_files.sh

Libc:
	mkdir -p "$(STAGE)/$@/dst" "$(STAGE)/$@/derived"
	cd sources/$@ && env -i PATH="$$PATH" SRCROOT="$$PWD" \
		DSTROOT="$(STAGE)/$@/dst" DERIVED_FILES_DIR="$(STAGE)/$@/derived" \
		ARCHS="$(ARCHS)" RC_ARCHS="$(ARCHS)" PLATFORM_NAME=macosx \
		VARIANT_PLATFORM_NAME=macosx DEPLOYMENT_LOCATION=YES \
		/bin/bash -e xcodescripts/headers.sh

AvailabilityVersions:
	mkdir -p "$(STAGE)/$@/dst"
	env -i PATH="$$PATH" $(MAKE) -C "sources/$@" installhdrs \
		DSTROOT="$(STAGE)/$@/dst" OBJROOT="$(STAGE)/$@/obj" \
		SYMROOT="$(STAGE)/$@/sym" CMAKE="$(CMAKE)" NINJA="$(NINJA)"
