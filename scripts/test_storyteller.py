import json
import os
import unittest
from unittest.mock import patch
from urllib.error import URLError

from chess_intelligence import ROOT, validate
from directors_cut import plan, SAMPLES
from story_provider import request_plan
from storyteller import catalog, choose, direct, disagreement, draft, validate_plan


class StorytellerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record=validate(json.loads((ROOT/"examples/analysis/deep-blue.json").read_text()))
        cls.moment=choose(cls.record,None)
        cls.deep={"ply":16,"best":cls.moment["recommended"],
                  "played":cls.moment["playedContinuation"],"estimatedLoss":.1365}

    def test_selects_ranked_candidate_or_override(self):
        self.assertEqual(self.moment["id"],"ply-16")
        self.assertEqual(choose(self.record,"ply-15")["id"],"ply-15")
        with self.assertRaises(ValueError):
            choose(self.record,"ply-999")

    def test_flags_material_disagreement(self):
        self.assertTrue(disagreement(.325,.1365,True))
        self.assertFalse(disagreement(.325,.30,True))
        self.assertTrue(disagreement(.325,.30,False))

    def test_output_cannot_inject_facts_or_moves(self):
        choices=catalog(self.record,self.deep)
        expected,_,_=draft(self.record,self.deep,"offline")
        for corrupt in (dict(expected, narration="Kasparov panicked."),
                        dict(expected, hook="This is forced mate."),
                        dict(expected, beats=["ply-14","invented-move","ply-16"]),
                        dict(expected, beats=["ply-16","ply-15","ply-17"])):
            with self.assertRaises(ValueError):
                validate_plan(corrupt,choices,"ply-16")

    def test_offline_determinism_and_hypothetical_line(self):
        a,beats,provider=draft(self.record,self.deep,"offline")
        self.assertEqual((a,beats,provider),draft(self.record,self.deep,"offline"))
        shots,claims=direct(self.record,self.deep,a,beats)
        self.assertEqual(provider["mode"],"offline-demonstration")
        self.assertTrue(any(shot.get("line")=="engine-choice" for shot in shots))
        self.assertTrue(any(c["category"]=="engine-hypothetical" for c in claims))
        for shot in shots:
            cues, duration, anchor=plan(shot,[60*SAMPLES]*len(shot["phrases"]))
            self.assertGreater(duration,cues[-1]["to"])
            if "anchor" in shot:
                self.assertGreater(anchor,cues[0]["from_"])

    def test_missing_credentials_and_provider_failure(self):
        with patch.dict(os.environ,{},clear=True), self.assertRaisesRegex(ValueError,"requires"):
            request_plan({})
        calls=[]
        def fail(_request,timeout):
            calls.append(timeout)
            raise URLError("unavailable")
        with patch.dict(os.environ,{"OPENROUTER_API_KEY":"test","STORY_MODEL":"test"},clear=True):
            with self.assertRaisesRegex(ValueError,"two attempts"):
                request_plan({},opener=fail,pause=lambda _:None)
        self.assertEqual(calls,[25,25])
