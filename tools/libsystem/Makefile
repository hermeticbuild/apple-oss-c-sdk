ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
.PHONY: check-interface
check-interface:
	@test -n "$(LLVM)" || { echo "Set LLVM to the official LLVM bundle directory" >&2; exit 2; }
	cd "$(ROOT)" && LLVM="$(abspath $(LLVM))" python3 -m unittest -v \
		tools.libsystem.test_interface tools.libsystem.test_libunwind_abi
