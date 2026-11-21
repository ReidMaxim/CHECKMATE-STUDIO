import math
import unittest

from live_direction import choose_treatment, treatments


class EditorialTreatmentTests(unittest.TestCase):
    def test_three_treatments_and_override(self):
        options=treatments({"ply":16})
        self.assertEqual(len({item["arc"] for item in options.values()}),3)
        self.assertEqual(choose_treatment(options),"choice")
        self.assertEqual(choose_treatment(options,"tempo"),"tempo")

    def test_raw_signal_gate(self):
        from voice_studio import signal
        clean=[.18*math.sin(i/20) for i in range(12000)]
        pcm,audit=signal(clean,24000)
        self.assertGreater(audit["rms"],.1)
        self.assertEqual(len(pcm),12000)
        for samples,rate,reason in (([0]*12000,24000,"Silent"),([float("nan")]*12000,24000,"Nonfinite"),
                                    ([1.0]*12000,24000,"clipping"),(clean,16000,"Invalid rate")):
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError,reason):
                signal(samples,rate)
