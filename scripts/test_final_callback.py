import unittest

import numpy as np

from casting_room import shortlist
from final_callback import FINALISTS, transient_flags


class CallbackTests(unittest.TestCase):
    def test_human_feedback_bypasses_technical_rank(self):
        self.assertEqual(shortlist({}, FINALISTS), ["george", "marius"])
        with self.assertRaises(ValueError):
            shortlist({}, ("george", "george"))

    def test_silence_and_late_impulse(self):
        self.assertEqual(transient_flags(np.zeros(12000), 24000), [])
        data = np.zeros(12000)
        data[8000] = .25
        self.assertTrue(transient_flags(data, 24000))
