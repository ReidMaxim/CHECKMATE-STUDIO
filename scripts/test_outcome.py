import unittest

from chess_intelligence import game_from
from outcome import review_outcome


class OutcomeTest(unittest.TestCase):
    def review(self, result, scope, *, refs=None, card=False, marker=None):
        pgn = f'[Result "{result}"]\n\n1. e4 e5 {result if marker is None else marker}'
        game = game_from(pgn)
        evidence = {"local": {"ply": 1, "claim": "e4"}}
        spec = {"kind": scope, "question": "What changes?", "payoff": "The pawn takes the center.",
                "payoffRefs": ["local"], "reason": "Answers the question", "card": card,
                "selected": "A", "options": {"A": {"text": "The pawn takes the center.", "refs":
                    refs if refs is not None else ["local"] + ([] if scope == "local" else ["recorded-result"])}}}
        return review_outcome(spec, pgn, [game, *game.mainline()], 1, evidence)

    def test_recorded_victory_while_film_stops_early(self):
        outcome = self.review("1-0", "recorded-victory", card=True)
        self.assertTrue(outcome["gameContinues"])
        self.assertEqual(outcome["game"]["lastMove"], "e5")
        self.assertEqual(outcome["card"]["score"], "1-0")
        self.assertIsNone(outcome["game"]["boardTermination"])

    def test_draw(self):
        self.assertEqual(self.review("1/2-1/2", "draw", card=True)["card"]["title"], "Draw")

    def test_local_lesson_omits_result_card(self):
        self.assertIsNone(self.review("0-1", "local")["card"])
        self.assertIsNone(self.review("*", "local")["game"]["claim"])
        with self.assertRaisesRegex(ValueError, "local lesson"):
            self.review("0-1", "local", card=True)

    def test_incomplete_or_contradictory_result_and_missing_claim(self):
        for result, scope, refs, marker in [("*", "draw", None, None), ("1-0", "recorded-victory", None, ""),
                                             ("1-0", "recorded-victory", ["local"], None),
                                             ("1-0", "recorded-victory", None, "0-1")]:
            with self.subTest(result=result, refs=refs, marker=marker), self.assertRaises(ValueError):
                self.review(result, scope, refs=refs, marker=marker)
