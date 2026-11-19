CMAKE ?= cmake
NINJA ?= ninja
SDK ?= macosx26.5
SOURCE_ROOT ?= $(CURDIR)/sources

availability_root = $(STAGE)/AvailabilityVersions
availability_source = $(SOURCE_ROOT)/AvailabilityVersions
availability_build_source = $(availability_source)
availability_header = usr/include/AvailabilityInternal.h
availability_rule = sources/AvailabilityVersions/CMakeLists.txt
availability_inputs = sources/AvailabilityVersions/Makefile \
	sources/AvailabilityVersions/availability sources/AvailabilityVersions/availability.dsl \
	$(availability_supplement)

ifeq ($(SDK),macosx26.5)
availability_build_source = $(availability_root)/src
availability_supplement = recipes/availability_versions/stage_dsl.py \
	recipes/availability_versions/macosx26.5.dsl
endif

.PHONY: stage-AvailabilityVersions
stage: stage-AvailabilityVersions
stage-AvailabilityVersions:
	mkdir -p "$(availability_root)/dst"
ifeq ($(SDK),macosx26.5)
	"$(PYTHON)" recipes/availability_versions/stage_dsl.py "$(availability_source)" "$(availability_build_source)"
endif
	env -i PATH="$$PATH" $(MAKE) -C "$(availability_build_source)" installhdrs \
		DSTROOT="$(availability_root)/dst" OBJROOT="$(availability_root)/obj" \
		SYMROOT="$(availability_root)/sym" CMAKE="$(CMAKE)" NINJA="$(NINJA)"
	"$(PYTHON)" recipes/availability_versions/headers.py "$(availability_root)/dst/$(availability_header)"
	$(call header-record,AvailabilityVersions,$(availability_header),staged:AvailabilityVersions:AvailabilityInternal.h,$(availability_rule),Apple public header install and add xros aliases,$(availability_rule) $(availability_inputs))
	$(call record-installed,AvailabilityVersions,$(availability_rule),usr/include,$(availability_header),$(availability_inputs))
