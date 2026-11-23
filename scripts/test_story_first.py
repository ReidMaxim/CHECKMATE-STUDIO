import json
import unittest

from chess_intelligence import ROOT
from story_first import review


class StoryFirstTest(unittest.TestCase):
    def setUp(self):
        self.brief = json.loads((ROOT / "examples/story-first/lasker-bauer.json").read_text())

    def test_both_scripts_trace_to_legal_game(self):
        _, nodes, evidence = review(self.brief)
        self.assertFalse(nodes[evidence["second"]["ply"]].board().is_check())
        self.assertEqual(evidence["queen-taken"]["claim"], "Rxh6+")

    def test_forged_move_fails_review(self):
        self.brief["facts"]["second"][-1] = "Bxg7+"
        with self.assertRaisesRegex(ValueError, "replay shows"):
            review(self.brief)

    def test_unknown_claim_and_skipped_ply_fail_review(self):
        self.brief["scripts"]["B"]["lines"][0][-1].append("made-up")
        with self.assertRaisesRegex(ValueError, "Untraceable"):
            review(self.brief)
        del self.brief["shots"]["38"]
        with self.assertRaisesRegex(ValueError, "consecutive"):
            review(self.brief)
