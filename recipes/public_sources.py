"""Public install-list checks for direct copies."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

XCODE_PUBLIC_HEADERS = {
    "sources/libpthread/include/pthread/pthread_impl.h": "libpthread/libpthread.xcodeproj/project.pbxproj",
    "sources/libpthread/include/pthread/pthread.h": "libpthread/libpthread.xcodeproj/project.pbxproj",
    "sources/libpthread/include/pthread/sched.h": "libpthread/libpthread.xcodeproj/project.pbxproj",
}


def public_xcode_selection(source: Path) -> str | None:
    try:
        relative = source.relative_to(ROOT).as_posix()
    except ValueError:
        return None
    project = XCODE_PUBLIC_HEADERS.get(relative)
    if project is None:
        return None
    marker = f"/* {source.name} in Headers */"
    lines = (ROOT / "sources" / project).read_text().splitlines()
    if not any(marker in line and "ATTRIBUTES = (Public," in line for line in lines):
        raise ValueError(f"public Xcode header phase changed: {relative}")
    return project + ":Public"


def architecture_public_headers() -> list[Path]:
    """Follow architecture/Makefile:copyhdrs for both supported CPU families."""
    makefile = (ROOT / "sources/architecture/Makefile").read_text()
    required = (
        "CANONICAL_ARCH_x86_64 = i386",
        "CANONICAL_ARCH_arm64 = arm",
        "DIRS = . $(ARCHS)",
        "EXPORT_DSTDIR=/usr/include/architecture",
        "copyhdrs: all DSTROOT",
        "install $(INSTALL_FLAGS) *.h $$DSTDIR",
    )
    if any(marker not in makefile for marker in required):
        raise ValueError("architecture public install rule changed")
    root = ROOT / "sources/architecture"
    paths = sorted(path.relative_to(root) for directory in (root, root / "arm", root / "i386")
                   for path in directory.glob("*.h"))
    if len(paths) != 19:
        raise ValueError(f"architecture public header list changed: {len(paths)}")
    return paths
