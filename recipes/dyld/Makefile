# dyld.xcodeproj/project.pbxproj macOS publicHeaders and configs/libdyld.xcconfig.
# Own fixup-chains.h here because XNU lists its version only as an export.
.PHONY: stage-dyld
stage: stage-dyld
stage-dyld:
	$(call copy-headers,dyld,.,sources/dyld/include/dlfcn.h)
	$(call copy-headers,dyld,mach-o,sources/dyld/include/mach-o/utils.h sources/dyld/include/mach-o/fixup-chains.h)
	"$(PYTHON)" recipes/dyld/headers.py "$(STAGE)/dyld/dst/usr/include/mach-o"
	$(call header-override,dyld,usr/include/mach-o/dyld.h,generated:apple via recipes/dyld/headers.py:mach-o/dyld.h,recipes/dyld/headers.py,guard missing ExclaveKit availability macro,sources/dyld/include/mach-o/dyld.h)
	$(call header-override,dyld,usr/include/mach-o/dyld_images.h,generated:mach-o/dyld_images.h via recipes/dyld/headers.py,generated explicit,add public dependency includes,sources/dyld/include/mach-o/dyld_images.h)
	$(call record-stage,dyld,recipes/dyld/Makefile)
