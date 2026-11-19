# Libm.xcodeproj/project.pbxproj Copy ARM and Copy Intel phases.
.PHONY: stage-Libm
stage: stage-Libm
stage-Libm:
ifeq ($(SDK),macosx26.5)
	mkdir -p "$(STAGE)/Libm/dst/usr/include/architecture/arm"
	"$(PYTHON)" recipes/libm/arm_math.py "$(SOURCE_ROOT)/Libm/Source/ARM" \
		"$(STAGE)/Libm/dst/usr/include/architecture/arm/math.h"
	$(call header-record,Libm,usr/include/architecture/arm/math.h,derived:sources/Libm/Source/ARM/math.h,recipes/libm/arm_math.py,inline the Apple binary64 classifier for macOS arm64 C,sources/Libm/Source/ARM/math.h sources/Libm/Source/ARM/fpclassify.c recipes/libm/arm_math.py)
else
	$(call copy-headers,Libm,architecture/arm,sources/Libm/Source/ARM/math.h,recipes/libm/Makefile)
endif
	$(call copy-headers,Libm,architecture/i386,sources/Libm/Source/Intel/math.h,recipes/libm/Makefile)
	"$(PYTHON)" recipes/libm/headers.py "$(STAGE)/Libm" "$(SDK)" >> "$(STAGE)/Libm/records"
