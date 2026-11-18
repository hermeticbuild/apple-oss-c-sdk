# dyld.xcodeproj/project.pbxproj macOS publicHeaders and configs/libdyld.xcconfig.
# Own fixup-chains.h here because XNU lists its version only as an export.
.PHONY: stage-dyld
stage: stage-dyld
stage-dyld:
	$(call copy-headers,dyld,.,sources/dyld/include/dlfcn.h)
	$(call copy-headers,dyld,mach-o,sources/dyld/include/mach-o/utils.h sources/dyld/include/mach-o/fixup-chains.h)
	$(call record-stage,dyld,recipes/dyld/Makefile)
