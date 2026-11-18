.PHONY: stage-xnu
stage: stage-xnu
stage-xnu:
	mkdir -p "$(STAGE)/xnu"
	"$(PYTHON)" recipes/xnu/headers.py "$(STAGE)/xnu" > "$(STAGE)/xnu/records"

# The Libsyscall public MIG list uses the armv7/i386 preprocessing modes.
.PHONY: mig-arm64 mig-x86_64
mig-arm64 mig-x86_64: pre-mig
	/bin/sh recipes/xnu/mig.sh "$(@:mig-%=%)" "$(MIG)" "$(CLANG)" "$(STAGE)/pre-mig" "$(STAGE)/$@"
