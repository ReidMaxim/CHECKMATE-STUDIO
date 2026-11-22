import unittest

from producer import check_lines, develop, select


class ProducerTests(unittest.TestCase):
    def test_selection_limits_and_override(self):
        candidates = [dict(key="reject", score=99, decision="reject"),
                      dict(key="revise", score=50, decision="revise"),
                      dict(key="produce", score=72, decision="produce"),
                      dict(key="lower", score=71, decision="produce")]
        self.assertEqual(select(candidates)["key"], "produce")
        self.assertEqual(select(candidates, "lower")["key"], "lower")
        self.assertIsNone(select(candidates, "reject"))
        self.assertIsNone(select(candidates[:2]))
        self.assertIsNone(select([]))

    def test_script_fact_boundaries(self):
        slots = [{"shot": 0, "allowed": ["main"]}]
        sentence = {"text":"The rook delivers mate.", "facts":["main"]}
        self.assertEqual(check_lines({"beats":[{"shot":0,"sentences":[sentence]}]}, slots)[0]["shot"], 0)
        for bad in ({"facts":["engine"]}, {"facts":[]}, {"text":"The king moves. Then it resigns."}):
            with self.assertRaises(ValueError):
                check_lines({"beats":[{"shot":0,"sentences":[{**sentence, **bad}]}]}, slots)

    def test_one_editor_pass_and_fail_closed_review(self):
        slot = {"text":"Original prose about this choice.", "refs":["main"], "line":"main", "title":"Decision"}
        draft = {"beats":[{"shot":0,"sentences":[{"text":"The rook delivers mate.","facts":["main"]}]}]}
        responses = [draft, {"notes":["The draft gets straight to the payoff."],"beats":None},
                     {"draftSupported":True,"finalSupported":False}]
        with self.assertRaisesRegex(ValueError, "factual review"):
            develop([slot], {"main":{"claim":"The rook delivers mate"}}, {}, True,
                    lambda *args, **kwargs: (responses.pop(0), {"model":"test"}))
        self.assertEqual(responses, [])
        self.assertEqual(slot["text"], "Original prose about this choice.")
