import copy
import unittest

import chess

from chess_intelligence import game_from
from unseen import ROOT, describe, fact_bank, offline_plan, rank_verified, titles, validate_treatments


class UnseenTest(unittest.TestCase):
    def test_both_scores_and_custom_black_position(self):
        for name, count in (("opera", 33), ("rook-ending", 103)):
            text = (ROOT / f"examples/unseen/{name}.pgn").read_text()
            self.assertEqual(len(list(game_from(text).mainline_moves())), count)
        pgn = '[SetUp "1"]\n[FEN "8/8/8/8/8/6k1/4p3/7K b - - 0 52"]\n\n52... e1=Q# 0-1'
        game = game_from(pgn)
        facts = fact_bank({"game": {"pgn": pgn}}, {"ply": 1, "estimatedLoss": 0})
        self.assertFalse(game.board().turn)
        self.assertEqual(facts["move-1"]["text"], "Black promotes to a queen on E1.")
        self.assertIn("checkmate", facts["check-1"]["text"])
        with self.assertRaises(ValueError):
            game_from(pgn.replace("e1=Q#", "e4"))

    def test_no_candidates_and_deep_reranking(self):
        self.assertEqual(rank_verified({"criticalMoments": [], "storyCandidates": []}, 16), [])
        board = chess.Board()
        make = lambda ply, score: dict(id=f"ply-{ply}", ply=ply, move="e4",
                                       score=score, afterFen=board.fen(), category="major-blunder")
        record = {"criticalMoments": [make(1, 95), make(4, 65)],
                  "storyCandidates": ["ply-1", "ply-4"]}
        def verify(_record, moment, _depth, _engine):
            return dict(estimatedLoss=.01 if moment["ply"] == 1 else .28,
                        after=None, played={"moves": [{"uci": "e2e4"}]},
                        best={"moves": [{"uci": "d2d4"}]})
        ranked = rank_verified(record, 16, verifier=verify)
        self.assertEqual([(item["moment"]["id"], item["eligible"]) for item in ranked],
                         [("ply-4", True), ("ply-1", False)])

    def test_unsupported_text_and_variation_relabeling(self):
        pgn = (ROOT / "examples/unseen/opera.pgn").read_text()
        board = game_from(pgn).board()
        deep = dict(ply=1, estimatedLoss=.2, best={"fen": board.fen(), "moves": [{"uci": "d2d4"}]},
                    played={"moves": [{"uci": "e2e4"}]})
        facts = fact_bank({"game": {"pgn": pgn}}, deep)
        labels = titles({"move": "e4"})
        response = offline_plan(facts, 1, labels)
        self.assertEqual(len(validate_treatments(response, facts, 1, labels, live=False)), 3)
        for field, value in (("hook", "White was afraid of defeat."),
                             ("script", ["move-1", "alt-1", "move-2"]),
                             ("script", ["move-2", "move-1"]),
                             ("script", ["move-1", "invented", "move-2"])):
            bad = copy.deepcopy(response)
            bad["treatments"][0][field] = value
            with self.assertRaises(ValueError):
                validate_treatments(bad, facts, 1, labels, live=False)


if __name__ == "__main__":
    unittest.main()
