import unittest
from directors_cut import MOVE_FRAMES, SAMPLES, plan, sound


class DirectorTimingTests(unittest.TestCase):
    def test_captions_follow_audio_and_move_occurs_inside_its_phrase(self):
        scene = {"lead": .2, "tail": .5, "phrases": [["Setup.", .3], ["The knight jumps.", 0]],
                 "anchor": 1, "title": "Reveal"}
        cues, duration, move = plan(scene, [20*SAMPLES+1, 50*SAMPLES])
        self.assertEqual([(cue["from_"], cue["to"]) for cue in cues], [(6,27), (36,86)])
        self.assertEqual(duration, 101)
        self.assertEqual(move, 42)
        self.assertLess(move + MOVE_FRAMES, 86)

    def test_short_anchor_and_oversized_caption_are_rejected(self):
        scene = {"lead": 0, "tail": 1, "phrases": [["Move.", 0]], "anchor": 0, "title": "Reveal"}
        with self.assertRaisesRegex(ValueError, "spoken phrase"):
            plan(scene, [12*SAMPLES])
        scene["phrases"][0][0] = "Long caption " * 9
        with self.assertRaisesRegex(ValueError, "safe budget"):
            plan(scene, [50*SAMPLES])

    def test_original_effect_is_deterministic_and_has_headroom(self):
        self.assertEqual(sound("capture"), sound("capture"))
        self.assertLess(max(map(abs, sound("capture"))), 5000)
