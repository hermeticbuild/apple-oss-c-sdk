CMAKE ?= cmake
NINJA ?= ninja

availability_root = $(STAGE)/AvailabilityVersions
availability_header = usr/include/AvailabilityInternal.h
availability_rule = sources/AvailabilityVersions/CMakeLists.txt
availability_inputs = sources/AvailabilityVersions/Makefile \
	sources/AvailabilityVersions/availability sources/AvailabilityVersions/availability.dsl

.PHONY: stage-AvailabilityVersions
stage: stage-AvailabilityVersions
stage-AvailabilityVersions:
	mkdir -p "$(availability_root)/dst"
	env -i PATH="$$PATH" $(MAKE) -C sources/AvailabilityVersions installhdrs \
		DSTROOT="$(availability_root)/dst" OBJROOT="$(availability_root)/obj" \
		SYMROOT="$(availability_root)/sym" CMAKE="$(CMAKE)" NINJA="$(NINJA)"
	"$(PYTHON)" recipes/availability_versions/headers.py "$(availability_root)/dst/$(availability_header)"
	$(call header-override,AvailabilityVersions,$(availability_header),staged:AvailabilityVersions:AvailabilityInternal.h,$(availability_rule),Apple public header install and add xros aliases,$(availability_rule) $(availability_inputs))
	$(call record-stage,AvailabilityVersions,$(availability_rule),$(availability_inputs))
