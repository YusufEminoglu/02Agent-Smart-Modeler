import json
import unittest

from zero2smartmodeler.core import recent_files


class RecentFilesTests(unittest.TestCase):
    def test_newest_first_without_duplicates_and_capped(self):
        paths = []
        for index in range(recent_files.MAX_RECENT + 3):
            paths = recent_files.add(paths, f"C:/work/w{index}.smartmodeler.json")
        self.assertEqual(len(paths), recent_files.MAX_RECENT)
        self.assertTrue(paths[0].endswith(f"w{recent_files.MAX_RECENT + 2}.smartmodeler.json"))
        again = recent_files.add(paths, paths[3])
        self.assertEqual(again[0], paths[3])
        self.assertEqual(len(again), len(set(again)))

    def test_only_workflow_files_are_remembered(self):
        self.assertEqual(recent_files.add([], "C:/work/script.py"), [])
        self.assertEqual(recent_files.add([], "C:/work/model.model3"), ["C:/work/model.model3"])

    def test_missing_files_are_hidden_and_bad_storage_is_empty(self):
        stored = recent_files.dumps(["a.model3", "b.model3"])
        self.assertEqual(recent_files.existing(recent_files.loads(stored), lambda p: p == "b.model3"),
                         ["b.model3"])
        self.assertEqual(recent_files.loads("not json"), [])
        self.assertEqual(recent_files.loads(json.dumps({"a": 1})), [])


if __name__ == "__main__":
    unittest.main()
