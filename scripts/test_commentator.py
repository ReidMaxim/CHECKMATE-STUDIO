import unittest

from commentator import choose_hook, perform, repetition


class CommentatorTests(unittest.TestCase):
    def test_hook_varies_with_mechanism(self):
        motif = dict(blockerName="knight", attackerName="rook", offeredName="queen")
        options = choose_hook("forced-clearance", motif, ())
        self.assertEqual({x["kind"] for x in options["candidates"]}, {"observation", "puzzle", "consequence"})
        self.assertEqual(options["selected"]["kind"], "observation")
        self.assertEqual(choose_hook("decision-contrast", None, ("F5","D1"))["selected"]["kind"], "puzzle")

    def test_edits_report_repetition_without_rejecting_it(self):
        stats = repetition(["Look at the rook. Now, wait.", "Look at the king. Now, wait."])
        self.assertEqual(stats["repeatedOpenings"]["look at"], 2)
        self.assertEqual(stats["now"], 2)
        self.assertEqual(stats["exactDuplicateSentences"], 1)

    def test_reveal_follows_move_landing(self):
        shot = {"preset":"reveal", "phrases":[["Straight to D8. That's mate.", 0]], "chapter":4, "visualMoveAt":1}
        rates, audit = perform([shot])
        self.assertGreater(shot["lead"], shot["visualMoveAt"] + 19 / 30)
        self.assertIn("D eight", shot["phrases"][0][2])
        self.assertEqual(len(rates), 1)
        self.assertEqual(audit[0]["direction"], "reveal")
