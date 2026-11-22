import unittest

from chess_intelligence import ROOT, game_from
from commentary_pass import build, forced_clearance, write_live
from directors_cut import caption_pages, plan


class CommentaryTest(unittest.TestCase):
    def test_combined_facts_and_mate_clearance(self):
        pgn = (ROOT / "examples/unseen/opera.pgn").read_text()
        nodes = list(game_from(pgn).mainline())
        self.assertIsNone(forced_clearance(nodes, 30))
        scenes, evidence, variation = build({"game": {"pgn": pgn}}, {"deep": {"ply": 33}})
        self.assertEqual([shot["ply"] for shot in scenes], [30, 31, 32, 33, 33])
        self.assertEqual(len(variation), 0)
        self.assertEqual(scenes[2]["refs"], ["move-32", "forced-capture", "cleared-route"])
        self.assertIn("sole blocker", evidence["cleared-route"]["claim"])

    def test_visual_only_move_and_long_caption(self):
        self.assertEqual(plan({"chapter": 1, "lead": .2, "tail": .9, "phrases": [],
                               "visualMoveAt": .2}, []), ([], 33, 6))
        scene = {"chapter": 1, "lead": .2, "tail": .9, "phrases": [
            ("This is a test sentence with enough words to produce multiple caption pages, while the voice stays continuous.", 0)]}
        cues, _, _ = plan(scene, [100_000])
        pages = caption_pages(cues, 1)
        self.assertEqual(" ".join(page["text"] for page in pages), scene["phrases"][0][0])
        self.assertEqual(pages[-1]["to"], cues[0]["to"])
        self.assertTrue(all(len(page["text"]) <= 58 for page in pages))

    def test_unapproved_hosted_rewrite_fails_closed(self):
        drafts = [{"text": "A question", "refs": [], "line": "main"}]
        returns = iter([({"lines":[{"shot":0,"text":"The queen gets captured next because that player feared losing the game."}]}, {}),
                        ({"accepted":[]}, {})])
        with self.assertRaisesRegex(ValueError, "entailment"):
            write_live(drafts, {}, lambda *args, **kwargs: next(returns))
        self.assertEqual(drafts[0]["text"], "A question")
