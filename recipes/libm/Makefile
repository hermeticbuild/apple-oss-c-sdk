# Libm.xcodeproj/project.pbxproj Copy ARM and Copy Intel phases.
.PHONY: stage-Libm
stage: stage-Libm
stage-Libm:
	$(call copy-headers,Libm,architecture/arm,sources/Libm/Source/ARM/math.h,recipes/libm/Makefile)
	$(call copy-headers,Libm,architecture/i386,sources/Libm/Source/Intel/math.h,recipes/libm/Makefile)
	"$(PYTHON)" recipes/libm/headers.py "$(STAGE)/Libm" >> "$(STAGE)/Libm/records"
