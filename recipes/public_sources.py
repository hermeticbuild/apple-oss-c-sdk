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
