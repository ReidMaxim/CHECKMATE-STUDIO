from array import array
import json
import unittest

from signature_voice import FIXTURE, align, discrepancies
from tts_providers import Speech


class SignatureVoiceTests(unittest.TestCase):
    def test_frozen_timeline_preserves_script_and_direction(self):
        reference = json.loads(FIXTURE.read_text())
        for original, audit, claim in zip(reference["project"]["scenes"], reference["timing"]["scenes"],
                                          reference["claims"], strict=True):
            audio = Speech(array("h", [200] * audit["spokenSamples"][0]), 24000, "test", "test",
                           "test", {}, {}, .1)
            shot = align(original, audit, audio, False)
            self.assertEqual(shot["phrases"][0][0], claim["text"])
            for key in ("title", "camera", "ply", "highlights", "transition", "chapter"):
                self.assertEqual(shot[key], original[key])
            if original["moveFrames"]:
                self.assertEqual(round(shot["visualMoveAt"] * 30), original["moveAt"])

    def test_audit_reports_real_sample_duration(self):
        speech = Speech(array("h", [200] * 12000), 24000, "test", "test", "test", {}, {}, .1)
        self.assertEqual(speech.audit()["durationSeconds"], .5)

    def test_asr_comparison_flags_omissions_and_repetitions(self):
        differences = discrepancies("That knight has to take", "that knight knight has to")
        self.assertEqual([(item["type"], item["expected"], item["recognized"]) for item in differences],
                         [("insert", "", "knight"), ("delete", "take", "")])
