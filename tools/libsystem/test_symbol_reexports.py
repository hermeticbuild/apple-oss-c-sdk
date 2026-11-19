import unittest

from .emit import ARCHES, SYSTEM, resolve
from .expected_undefined import filter_demands, policy_for
from .libc_aliases import LIBC, PLATFORM, forwarding_record


def image(name, children):
    return {"install_name": name, "current_version": "1", "compatibility_version": "1",
            "slices": {arch: {"exports": {}, "reexports": children} for arch in ARCHES}}


class SymbolReexports(unittest.TestCase):
    def setUp(self):
        self.libc = image(LIBC, [])
        self.images = [image(SYSTEM, [LIBC, PLATFORM]), self.libc, image(PLATFORM, [])]
        self.demands = {arch: [{"symbol": "_memcpy", "kind": "function", "header": "string.h"}] for arch in ARCHES}
        for part in self.libc["slices"].values():
            part["symbol_reexports"] = {"_memcpy": forwarding_record("__platform_memmove")}

    def test_public_name_is_reexported_and_implementation_retained_in_receipt(self):
        tbd, rows = resolve(self.images, self.demands, "11.0")
        doc = next(x for x in tbd["libraries"] if x["install_names"][0]["name"] == LIBC)
        self.assertNotIn("exported_symbols", doc)
        self.assertEqual([g["text"]["global"] for g in doc["reexported_symbols"]], [["_memcpy"], ["_memcpy"]])
        self.assertEqual([(r["arch"], r["provider"], r["target_library"], r["target_symbol"]) for r in rows],
                         [(arch, LIBC, PLATFORM, "__platform_memmove") for arch in ARCHES])

    def test_forwarding_requires_a_reachable_destination_on_that_arch(self):
        self.images[0]["slices"]["x86_64"]["reexports"] = [LIBC]
        del self.images[2]["slices"]["x86_64"]
        with self.assertRaisesRegex(ValueError, "x86_64: invalid forwarding destination"):
            resolve(self.images, self.demands, "11.0")

    def test_undefined_exemption_also_rejects_a_forwarding_component(self):
        self.libc["slices"]["arm64"]["symbol_reexports"]["_profil"] = forwarding_record("_example")
        with self.assertRaisesRegex(ValueError, "reopen.*_profil"):
            filter_demands(policy_for("macosx26.5"), self.images, {})
