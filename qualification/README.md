# Qualification and LLVM composition

`check_c_profile.py` compiles the 174 checked-in roots individually and
together, plus semantic fixtures, for arm64 and x86_64 with `-nostdinc`. Only
the pinned Clang resource directory and the produced C installation are
visible. `check_libunwind_headers.py` verifies separately supplied LLVM
runtime headers. `compose_sdk.py` joins the C installation with Apple SDK Gen
link assets and framework headers, LLVM libc++, LLVM libunwind, and the
temporary archived CoreFoundation header layer. `validate_llvm.py` archives
that composition and builds `@llvm-project//llvm:llvm` on both macOS targets.

Root-level script names are compatibility command entry points. Their
implementations live here so production, audit, and qualification have
separate code paths.
