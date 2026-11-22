import unittest

from casting_room import score, shortlist


class CastingTests(unittest.TestCase):
    def test_machine_screen_ignores_homophones_not_omissions(self):
        self.assertEqual(score({"differences":[
            {"expected":"knight", "recognized":"night"}, {"expected":"sacrifice", "recognized":""}
        ]}), 1)

    def test_shortlist_ranks_candidates_and_excludes_references(self):
        candidates = {name: {"score": score, "seconds": 18}
                      for name, score in [("alba",0), ("marius",1), ("javert",2), ("george",3)]}
        self.assertEqual(shortlist(candidates), ["marius", "javert"])
