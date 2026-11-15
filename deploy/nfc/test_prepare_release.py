import argparse
import json
import tempfile
import unittest
from pathlib import Path

from prepare_release import fingerprint, merged_links, prepare, validated_base


class ReleasePreparationTests(unittest.TestCase):
    def test_https_path_and_fingerprint(self):
        self.assertEqual(validated_base("https://example.test/aicardhub/"), "https://example.test/aicardhub")
        self.assertEqual(len(fingerprint("ab" * 32).split(":")), 32)
        for invalid in ["http://example.test", "https://u:p@example.test", "https://example.test/a/../b", "https://example.test/a?b=1",
                        "https://example.test:443/aicardhub", "https://example.test:bad/aicardhub",
                        "https://example.test:/aicardhub", "https://example.test/a.b", "https://example.test/a//b"]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validated_base(invalid)

    def test_preserves_original_associations_and_idempotent_merge(self):
        original = [{"relation": ["other-relation"], "target": {"namespace": "web", "site": "https://example.test"}}]
        merged = merged_links(original, "cn.aicardhub.nfc", "ab" * 32)
        self.assertEqual(merged[0], original[0])
        self.assertEqual(len(original), 1)
        self.assertEqual(merged_links(merged, "cn.aicardhub.nfc", "ab" * 32), merged)

    def test_prepares_exact_bytes_and_never_overwrites_existing_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "candidate.apk"
            source.write_bytes(b"synthetic-apk-only-for-metadata-test")
            args = argparse.Namespace(apk=source, package_id="cn.aicardhub.nfc", certificate_sha256="ab" * 32,
                                      public_base_url="https://example.test/aicardhub", existing_assetlinks=None,
                                      output_dir=root / "release", channel="debug-test")
            prepare(args)
            metadata = json.loads((args.output_dir / "release.json").read_text())
            self.assertEqual(metadata["app_link_path"], "/aicardhub/share/nfc")
            self.assertEqual((args.output_dir / metadata["apk"]).read_bytes(), source.read_bytes())
            with self.assertRaises(ValueError):
                prepare(args)


if __name__ == "__main__":
    unittest.main()
