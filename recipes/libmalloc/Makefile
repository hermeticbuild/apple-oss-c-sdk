# libmalloc.xcodeproj/project.pbxproj public headers and xcodeconfig/libmalloc.xcconfig.
# The pinned xcodescripts/sanitise_headers.sh contains no transformations.
.PHONY: stage-libmalloc
stage: stage-libmalloc
stage-libmalloc:
	$(call copy-headers,libmalloc,malloc,sources/libmalloc/include/malloc/_malloc.h \
		sources/libmalloc/include/malloc/_malloc_type.h \
		sources/libmalloc/include/malloc/_platform.h \
		sources/libmalloc/include/malloc/_ptrcheck.h \
		sources/libmalloc/include/malloc/malloc.h)
