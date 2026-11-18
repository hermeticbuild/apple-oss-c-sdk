# Libm.xcodeproj/project.pbxproj Copy ARM and Copy Intel phases.
.PHONY: stage-Libm
stage: stage-Libm
stage-Libm:
	$(call copy-headers,Libm,architecture/arm,sources/Libm/Source/ARM/math.h)
	$(call copy-headers,Libm,architecture/i386,sources/Libm/Source/Intel/fenv.h sources/Libm/Source/Intel/math.h)
	$(call record-stage,Libm,recipes/libm/Makefile)
