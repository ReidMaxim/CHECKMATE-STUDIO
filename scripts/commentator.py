"""Commentary editing and delivery controls for replay-backed stories."""
from collections import Counter
from copy import deepcopy
import re

from storyteller import spoken

VOICE_GUIDE = (
    "Explain the position like an enthusiastic chess player talking to a friend. Be observant and curious. "
    "Let the board do some of the talking. Prefer concrete pieces, squares and consequences to hype. "
    "Use contractions and vary sentence length. Avoid forced jokes, imagined motives, quotes and eyewitness claims. "
    "Build from setup to discovery when useful. One real question is enough."
)

# Kokoro supports speed and punctuation. Leads and tails are board observation time in seconds.
DELIVERY = {
    "establishing": ("conversational", .98, .16, .68),
    "critical": ("anticipatory", .96, .36, 1.16),
    "threat": ("explanatory", .99, .27, .55),
    "variation": ("explanatory", .98, .26, .55),
    "reveal": ("reveal", .93, 1.02, .48),
    "final": ("reflective", .95, .40, 1.08),
}


def choose_hook(angle, motif, decision):
    if angle == "forced-clearance":
        blocker, attacker = motif["blockerName"], motif["attackerName"]
        choices = [
            ("puzzle", f"How would you get that {blocker} out of the {attacker}'s way?", 3,
             "Specific, but a viewer needs time to identify the route before solving it."),
            ("consequence", f"The queen is about to be taken. That capture opens a path for the {attacker}."
             if motif["offeredName"] == "queen" else
             f"A {motif['offeredName']} is about to be taken. That capture opens a path for the {attacker}.", 4,
             "The consequence is concrete, but it gives away the mechanism early."),
            ("observation", f"That {blocker} is parked right in the {attacker}'s path. Keep its square in mind.", 5,
             "The highlighted board immediately supports the premise and leaves the answer open."),
        ]
    else:
        actual, alternative = decision
        choices = [
            ("puzzle", "Pick a move here. Then see if you'd stick with it after you see the game.", 5,
             "The comparison actually gives the viewer a chance to test their choice."),
            ("consequence", "The game went one way. Stockfish points to a different move from the same board.", 3,
             "Promises a comparison but gives the viewer less to do."),
            ("observation", f"Keep {actual} and {alternative} in mind. We're going to try both from this position.", 4,
             "Specific, but two square names add load before the position is introduced."),
        ]
    candidates = [dict(kind=kind, text=text, score=score, reason=reason) for kind, text, score, reason in choices]
    return {"candidates": candidates, "selected": max(candidates, key=lambda hook: hook["score"])}


def repetition(script):
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(script))
    words = re.findall(r"[a-z]+(?:'[a-z]+)?", " ".join(script).lower())
    openings = Counter(" ".join(re.findall(r"[a-z]+", line.lower())[:2]) for line in sentences if line.strip())
    pieces = Counter(word for word in words if word in {"rook", "bishop", "pawn", "knight", "queen", "king"})
    return {"repeatedOpenings": {key: count for key, count in openings.items() if count > 1},
            "now": words.count("now"), "lookAt": openings.get("look at", 0),
            "pieceMentions": dict(pieces),
            "moveRecitals": sum(bool(re.match(r"^(White|Black)(?: moves|['’]s .* takes)", line))
                                for line in sentences),
            "exactDuplicateSentences": len(sentences) - len(set(line.lower().strip() for line in sentences))}


def edit(drafts, evidence, angle, motif, squares):
    original = [{"shot": i, "text": shot["text"], "facts": list(shot["refs"])}
                for i, shot in enumerate(drafts) if shot["text"]]
    revised = deepcopy(original)
    hooks = choose_hook(angle, motif, squares)
    revised[0]["text"] = hooks["selected"]["text"]
    if motif:
        offered, attacker = motif["offeredName"], motif["attackerName"]
        square = motif["landing"]
        revised[1]["text"] = (f"So White gives up the {offered} with check. Before the capture, "
                             "see if you can spot another reply." if motif["color"] == "white" else
                             f"So Black gives up the {offered} with check. Before the capture, "
                             "see if you can spot another reply.")
        revised[2]["text"] = (f"Taking it is the only legal reply. And there's the catch. "
                             f"The {attacker} suddenly has a clear run.")
        revised[3]["text"] = f"Straight through to {square}. That's mate."
        revised[4]["text"] = (f"The {offered} was bait. The square the defender left behind was the real prize.")
        revised[4]["facts"] = ["forced-capture", "cleared-route"]
        notes = ["Point to the blocker before introducing the offer.",
                 "Replace the capture announcement with the reason it matters.",
                 "Let the mating move land before speaking, then return to the vacated square in the ending."]
    else:
        revised[1]["text"] = (f"The game goes to {squares[0]}. Keep that position in mind, because "
                              "the comparison starts one move earlier.")
        consequences = [key for key in revised[1]["facts"] if key == "check"]
        if consequences:
            claim = evidence["check"]["claim"]
            revised[1]["text"] += " That's checkmate." if "checkmate" in claim else " The king is in check."
        revised[2]["text"] = "Back up one move. Same pieces, same side to play. What would you change?"
        revised[3]["text"] = f"Stockfish prefers the move to {squares[1]}. See how it starts from exactly the same position?"
        revised[4]["text"] = ("Here’s the game position again. When a move looks natural, compare your two ideas "
                              "from the same board before following either line.")
        notes = ["Invite a concrete choice before showing the game.",
                 "Label the engine alternative and return to the recorded position for the takeaway."]
    for beat in revised:
        drafts[beat["shot"]].update(text=beat["text"], refs=beat["facts"])
    return dict(mode="offline-composed", original=original, revised=revised, notes=notes, hooks=hooks,
                indicators={"draft": repetition([beat["text"] for beat in original]),
                            "final": repetition([beat["text"] for beat in revised])},
                changed=original != revised, revisionPasses=1)


def perform(scenes):
    audit, rates = [], {}
    for scene in scenes:
        if not scene["phrases"]:
            continue
        direction, rate, lead, tail = DELIVERY[scene["preset"]]
        text = scene["phrases"][0][0]
        utterance = spoken(text)
        scene["phrases"] = [[text, 0, utterance]]
        scene["lead"], scene["tail"] = lead, tail
        rates[utterance] = rate
        reason = "Let the voice finish one connected thought."
        if scene["preset"] == "critical":
            reason = "Hold the checked position so viewers can look for another reply."
            if "visualMoveAt" in scene:
                scene["visualMoveAt"] = lead + .65
        if scene["preset"] == "reveal" and "visualMoveAt" in scene:
            scene["visualMoveAt"] = .15
            reason = "Let the decisive move finish before explaining the payoff."
        if scene["preset"] == "final":
            reason = "Hold the final board through the takeaway."
        audit.append(dict(chapter=scene["chapter"], direction=direction, requestedRate=rate,
                          leadSeconds=lead, tailSeconds=tail, moveStartsAt=scene.get("visualMoveAt"), reason=reason))
    return rates, audit
