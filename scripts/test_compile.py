import copy
import json
import unittest

from compile import ROOT, compile_project, parse, position


class TestChessCompilation(unittest.TestCase):
    def setUp(self):
        self.sample = json.loads((ROOT / "projects/legal-mate.json").read_text())

    def test_real_line_and_forced_reply(self):
        frames = parse(self.sample["pgn"])
        self.assertEqual(len(frames), 14)
        self.assertEqual(frames[10]["move"]["capture"], "d1")
        self.assertEqual(frames[11]["legal"], 1)
        self.assertEqual(frames[12]["move"]["san"], "Ke7")
        self.assertTrue(frames[13]["mate"])

    def test_legal_and_invalid_fen(self):
        self.assertEqual(position("7k/P7/8/8/8/8/8/K7 w - - 0 1").piece_at(48).symbol(), "P")
        for fen in ("bad", "8/8/8/8/8/8/8/8 w - - 0 1"):
            with self.subTest(fen=fen), self.assertRaises(ValueError):
                position(fen)

    def test_illegal_and_malformed_pgn(self):
        for pgn in ("1. e4 e5 2. e6", "1. e4 nonsense e5"):
            with self.subTest(pgn=pgn), self.assertRaises(ValueError):
                parse(pgn)

    def test_promotion(self):
        compiled = parse('[SetUp "1"]\n[FEN "7k/P7/8/8/8/8/8/K7 w - - 0 1"]\n\n1. a8=Q+ *')
        self.assertEqual(compiled[-1]["pieces"]["a8"], "Q")

    def test_en_passant(self):
        compiled = parse("1. e4 a6 2. e5 d5 3. exd6")
        self.assertEqual(compiled[-1]["move"]["capture"], "d5")

    def test_castling(self):
        compiled = parse("1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O")
        self.assertEqual(compiled[-1]["move"]["rook"], ["h1", "f1"])

    def test_variation(self):
        self.sample["variations"] = {"declines": {"fromPly": 9, "moves": ["dxe5"]}}
        self.assertEqual(compile_project(self.sample)["lines"]["declines"][-1]["move"]["san"], "dxe5")

    def test_discontinuous_animation_and_missing_audio(self):
        invalid = copy.deepcopy(self.sample)
        invalid["scenes"][2]["ply"] = 12
        with self.assertRaisesRegex(ValueError, "advance one ply"):
            compile_project(invalid)
        self.sample["audio"][0]["asset"] = "absent.wav"
        with self.assertRaisesRegex(ValueError, "Missing"):
            compile_project(self.sample)
