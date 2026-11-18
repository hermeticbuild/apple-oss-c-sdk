.PHONY: stage-architecture
stage: stage-architecture
stage-architecture:
	mkdir -p "$(STAGE)/architecture/dst"
	env -i PATH="$$PATH" $(MAKE) -C sources/architecture installhdrs \
		DSTROOT="$(STAGE)/architecture/dst" RC_ARCHS="arm64 x86_64"
	$(call record-stage,architecture,sources/architecture/Makefile)
