"""Speech engines for the shared validated PCM and documentary timeline."""
from array import array
from dataclasses import dataclass
from importlib.metadata import version
from importlib.resources import files
from typing import Protocol
import json
import time

from directors_cut import RATE, ROOT
from voice_studio import VoiceStudio, signal

MODEL_REVISION = "d29db7978e464fb90cb3359ee0c69a273b9142cc"
POCKET_VOICES = ("alba", "anna")
CASTING_PROFILES = json.loads((ROOT / "examples/signature/casting-profiles.json").read_text())


@dataclass
class Speech:
    pcm: array
    sample_rate: int
    provider: str
    model: str
    voice: str
    settings: dict
    quality: dict
    generation_seconds: float

    def audit(self):
        return dict(sampleRate=self.sample_rate, durationSeconds=len(self.pcm) / self.sample_rate,
                    provider=self.provider, model=self.model, voice=self.voice, settings=self.settings,
                    quality=self.quality, generationSeconds=round(self.generation_seconds, 3))


class Narrator(Protocol):
    def synthesize(self, text: str) -> Speech: ...


class KokoroNarrator:
    def __init__(self, directory, voice, rates):
        self.studio = VoiceStudio(directory, voice, rates, model_file="kokoro-v1.0.onnx")

    def synthesize(self, text):
        started = time.monotonic()
        pcm = self.studio(text)
        result = self.studio.audit[-1]
        return Speech(pcm, result["sampleRate"], "kokoro", "Kokoro 82M v1.0 FP32", result["voice"],
                      {"rate": result["rate"], "requestedRate": result["requestedRate"], "profile": result["profile"]},
                      result, time.monotonic() - started)


class PocketNarrator:
    """Use only official precomputed voices with the corresponding pinned English model."""
    def __init__(self, voice, directory, *, temperature=.3, seeds=(42, 43)):
        if not 0 < temperature <= 1 or not 1 <= len(seeds) <= 2:
            raise ValueError("Expected positive temperature and one or two seeds")
        self.temperature, self.seeds = temperature, tuple(seeds)
        if voice not in (*POCKET_VOICES, *CASTING_PROFILES):
            raise ValueError("Pocket review profiles are limited to the listed upstream voices")
        import torch
        import yaml
        from pocket_tts import TTSModel

        torch.set_num_threads(2)
        self.torch = torch
        self.voice = voice
        self.model_version = f"Pocket TTS {version('pocket-tts')} English {MODEL_REVISION}"
        config = yaml.safe_load(files("pocket_tts").joinpath("config/english.yaml").read_text())
        config["weights_path"] = str((directory / "model.safetensors").resolve())
        config["weights_path_without_voice_cloning"] = None
        config["flow_lm"]["lookup_table"]["tokenizer_path"] = str((directory / "tokenizer.model").resolve())
        config_file = directory / "pocket-english-pinned.yaml"
        config_file.write_text(yaml.safe_dump(config))
        self.model = TTSModel.load_model(config=config_file, temp=temperature)
        self.state = self.model.get_state_for_audio_prompt(
            directory / f"{voice}.safetensors")

    def synthesize(self, text, *, capture=None):
        started = time.monotonic()
        errors = []
        for seed in self.seeds:
            try:
                self.torch.manual_seed(seed)
                samples = self.model.generate_audio(self.state, text)
                raw = samples.detach().cpu().numpy()
                pcm, quality = signal(raw, self.model.sample_rate)
                if capture is not None:
                    capture(raw, self.model.sample_rate)
                if self.model.sample_rate != RATE:
                    raise ValueError("Unexpected Pocket native sample rate")
                quality["attempts"] = errors
                return Speech(pcm, self.model.sample_rate, "pocket", self.model_version, self.voice,
                              {"temperature": self.temperature, "seed": seed, "nativeRate": True},
                              quality, time.monotonic() - started)
            except (ValueError, RuntimeError) as error:
                errors.append(str(error))
        raise ValueError(f"Pocket {self.voice} failed signal checks after two attempts: {errors}")
