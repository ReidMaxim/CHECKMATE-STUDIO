"""Validate raw Kokoro signal before it can enter the documentary timeline."""
from array import array
from math import sqrt

from directors_cut import RATE, trim


def signal(samples, rate):
    from math import isfinite

    if rate != RATE or getattr(samples,"ndim",1) != 1 or not RATE // 5 <= len(samples) <= 30 * RATE:
        raise ValueError("Invalid rate, shape, or duration")
    values = [float(sample) for sample in samples]
    if not all(isfinite(value) for value in values):
        raise ValueError("Nonfinite ONNX output before writing or encoding")
    peak = max(map(abs,values))
    rms = sqrt(sum(value*value for value in values)/len(values))
    clipped = sum(abs(abs(value)-1) < 1e-7 for value in values)/len(values)
    if peak < .02 or rms < .004:
        raise ValueError(f"Silent ONNX output before writing or encoding (peak={peak:.5f}, rms={rms:.5f})")
    if clipped > .001:
        raise ValueError(f"Excessive clipping in raw ONNX output ({clipped:.4%})")
    if peak > 2:
        raise ValueError(f"Unstable synthesis amplitude: peak={peak:.3f}")
    # Floating-point excursions can be scaled before PCM quantization.
    gain=min(1., .94/peak)
    pcm = trim(array("h", (round(32767 * gain * value) for value in values)))
    quiet = 0
    for start in range(0,len(pcm)-2400,2400):
        level = max(map(abs,pcm[start:start+2400]))
        quiet = quiet+1 if level < 70 else 0
        if quiet>=12:
            raise ValueError("Unexpected internal silence in narrated phrase")
    return pcm, {"sampleRate":rate,"samples":len(pcm),"rawSeconds":len(values)/rate,
                 "peak":round(peak,5),"rms":round(rms,5),"clippedFraction":clipped,"pcmGain":round(gain,5)}


class VoiceStudio:
    def __init__(self, model_dir, voice, rates):
        self.directory, self.voice, self.rates=model_dir,voice,rates
        self.audit=[]
        self.sessions={}
        self.preferred="portable"

    def engine(self, profile):
        if profile not in self.sessions:
            import onnxruntime as ort
            from kokoro_onnx import Kokoro

            options=ort.SessionOptions()
            options.intra_op_num_threads=1
            options.inter_op_num_threads=1
            if profile=="portable":
                options.graph_optimization_level=ort.GraphOptimizationLevel.ORT_DISABLE_ALL
            session=ort.InferenceSession(str(self.directory/"kokoro-v1.0.int8.onnx"),options,
                                         providers=["CPUExecutionProvider"])
            self.sessions[profile]=Kokoro.from_session(session,str(self.directory/"voices-v1.0.bin"))
        return self.sessions[profile]

    def __call__(self, text):
        rate=self.rates.get(text,1.0)
        attempts=[]
        sequence=[(self.preferred,rate),("portable",rate),("standard",rate),
                  ("portable",1.0),("portable",.96)]
        for profile,effective_rate in dict.fromkeys(sequence):
            try:
                samples,hz=self.engine(profile).create(text,voice=self.voice,speed=effective_rate,lang="en-us",trim=False)
                pcm,stats=signal(samples,hz)
            except (ValueError,RuntimeError) as exc:
                attempts.append({"profile":profile,"rate":effective_rate,"error":str(exc)})
                continue
            self.preferred=profile
            self.audit.append({"text":text,"voice":self.voice,"rate":effective_rate,"requestedRate":rate,"profile":profile,
                               "attempts":attempts,**stats})
            return pcm
        raise ValueError(f"Kokoro failed for {text!r}: {attempts}")
