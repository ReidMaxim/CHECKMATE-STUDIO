import copy
import json
import unittest

from arcade_audio import ROOT, validate_arcade
from chess_intelligence import game_from


class ArcadeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.evidence = json.loads((ROOT/"examples/analysis/legal-mate.json").read_text())
        self.cues = json.loads((ROOT/"src/arcade-cues.json").read_text())

    def test_uses_same_recorded_position_as_the_documentary(self):
        validate_arcade(self.evidence, self.cues)
        original = game_from((ROOT/"projects/legal-mate.pgn").read_text())
        states = [original.board(), *(node.board() for node in original.mainline())]
        self.assertEqual([row["fen"] for row in self.evidence["positions"][8:14]],
                         [board.fen() for board in states[8:14]])
        self.assertTrue(states[13].is_checkmate())

    def test_rejects_burst_outside_its_cue(self):
        broken = copy.deepcopy(self.cues)
        broken[1]["hit"] = 12
        with self.assertRaisesRegex(ValueError, "effect exceeds"):
            validate_arcade(self.evidence, broken)
