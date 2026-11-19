# libmalloc.xcodeproj/project.pbxproj public headers and xcodeconfig/libmalloc.xcconfig.
# The pinned xcodescripts/sanitise_headers.sh contains no transformations.
malloc_type_header = libmalloc/include/malloc/_malloc_type.h
malloc_type_dst = usr/include/malloc/_malloc_type.h

.PHONY: stage-libmalloc
stage: stage-libmalloc
stage-libmalloc:
	$(call copy-headers,libmalloc,malloc,sources/libmalloc/include/malloc/_malloc.h \
		sources/libmalloc/include/malloc/_platform.h \
		sources/libmalloc/include/malloc/_ptrcheck.h \
		sources/libmalloc/include/malloc/malloc.h)
ifeq ($(SDK),macosx26.5)
	# Apple's tests/malloc_type_backdeploy.c selects this public SDK branch.
	/usr/bin/unifdef -x2 -D__APPLE_BLEACH_SDK__ -o "$(STAGE)/libmalloc/dst/$(malloc_type_dst)" \
		"$(SOURCE_ROOT)/$(malloc_type_header)"
	$(call header-record,libmalloc,$(malloc_type_dst),derived:sources/$(malloc_type_header),recipes/libmalloc/Makefile,select public SDK backdeployment branch,sources/$(malloc_type_header) sources/libmalloc/tests/malloc_type_backdeploy.c recipes/libmalloc/Makefile)
else
	$(call copy-headers,libmalloc,malloc,sources/$(malloc_type_header))
endif
