"""Record advisory transcript discrepancies for the delivered narration."""
import json
from pathlib import Path
import sys

from vosk import Model, SetLogLevel

from signature_voice import recognize
from storyteller import spoken

output, models = map(Path, sys.argv[1:])
script = json.loads((output / "scripts.json").read_text())
timing = json.loads((output / "timing.json").read_text())
expected = " ".join(spoken(phrase["text"]) for scene in timing["scenes"] for phrase in scene["phrases"])
if not expected.endswith(spoken(script["ending"]["text"])):
    raise ValueError("The timing audit does not end with the approved text")
SetLogLevel(-1)
audit = recognize(Model(str(models / "vosk-model-small-en-us-0.15")), output / "george-narration.wav", expected)
(output / "transcript-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
