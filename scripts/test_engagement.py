import unittest

from chess_intelligence import ROOT, game_from
from engagement import design


class EngagementTests(unittest.TestCase):
    def test_three_story_types_and_none(self):
        opera = list(game_from((ROOT / "examples/unseen/opera.pgn").read_text()).mainline())
        rook = list(game_from((ROOT / "examples/unseen/rook-ending.pgn").read_text()).mainline())
        mate = {"deep": {"ply": 33}}
        choice = {"deep": {"ply": 66, "best": {"moves": [{"uci": "e3d1"}]}}}
        self.assertEqual(design(opera, mate, "forced-clearance")["selected"]["type"], "prediction")
        self.assertEqual(design(rook, choice, "decision-contrast")["selected"]["type"], "choice")
        endgame = {"deep": {"ply": 100}}
        self.assertEqual(design(rook, endgame, "positional-lesson")["selected"]["type"], "reflection")
        self.assertEqual(design(rook, choice, "decision-contrast", suppress=True)["selected"]["type"], "none")
        choice["deep"]["best"]["moves"][0]["uci"] = "a1h8"
        self.assertEqual(design(rook, choice, "decision-contrast")["selected"]["type"], "none")
