"""Optional release packaging for Producer's Room productions."""
import json

import chess

from commentary_pass import piece_name
from engagement import design
from tts_providers import KokoroNarrator, PocketNarrator, ROOT

CHANNEL = ROOT / "examples/signature/channel.json"


def direct(output, game, selected, winner, project, live):
    identity = json.loads(CHANNEL.read_text())
    nodes = list(game.mainline())
    plan = design(nodes, selected, winner["angle"])
    (output / "engagement.json").write_text(json.dumps(plan, indent=2) + "\n")
    (output / "channel.json").write_text(CHANNEL.read_text())
    pivot = selected["deep"]["ply"]
    move = nodes[pivot-1].move
    board = nodes[pivot-1].parent.board()
    piece = piece_name(board.piece_at(move.from_square))
    target = chess.square_name(move.to_square).upper()
    headline = f"The {piece.title()} Choice on {target}"
    if winner["angle"] == "forced-clearance":
        headline = f"The Capture That Clears the Way"
    project["title"] = headline
    project["branding"] = {key: identity[key] for key in ("wordmark", "accent", "typography")}
    project["branding"]["opening"] = "minimal"
    attribution = f"{game.headers['White']} vs. {game.headers['Black']} · {game.headers['Event']}"
    comment = next((option["wording"] for option in plan["candidates"] if option["placement"] == "pinned-comment"), None)
    copy = {"recommendedTitle": headline,
            "titles": [headline, f"What Would You Play? · {attribution.split(' · ')[0]}",
                       f"One Position, Two Ideas · {game.headers['White']} vs. {game.headers['Black']}"],
            "description": f"A short chess documentary about {attribution}. Game score: {game.headers.get('Source', '')}\n\n"
                           + identity["credit"] + "\n\n#Chess #ChessAnalysis",
            "pinnedComment": comment, "game": attribution, "source": game.headers.get("Source"), "voiceCredit": identity["credit"],
            "writing": "hosted-original" if live else "offline-composed",
            "release": "Creative approval pending"}
    (output / "publication.json").write_text(json.dumps(copy, indent=2, ensure_ascii=False) + "\n")
    return identity


def synthesize(identity, directory, rates, texts):
    settings = identity["narrator"]
    try:
        studio = PocketNarrator(settings["voice"], directory)
        clips = {text: studio.synthesize(text) for text in texts}
        fallback = None
    except (OSError, RuntimeError, ValueError) as error:
        studio = KokoroNarrator(ROOT / ".cache/kokoro", settings["fallback"]["voice"], rates)
        clips = {text: studio.synthesize(text) for text in texts}
        fallback = str(error)
    return clips, fallback


def enrich(game, selected, drafts, evidence):
    """Show the recorded tactical consequence when it explains the comparison."""
    pivot = selected["deep"]["ply"]
    nodes = list(game.mainline())
    if pivot >= len(nodes) or not any(shot["line"] == "engine-choice" for shot in drafts):
        return
    move, reply = nodes[pivot-1].move, nodes[pivot]
    board = reply.parent.board()
    if not board.is_capture(reply.move) or reply.move.to_square != move.to_square:
        return
    taking = piece_name(board.piece_at(reply.move.from_square))
    taken = piece_name(board.piece_at(reply.move.to_square))
    square = chess.square_name(reply.move.to_square).upper()
    key = "recorded-payoff"
    text = f"The {taking} can take the {taken} on {square}. Here's what that looks like."
    evidence[key] = {"claim": f"Recorded {reply.san()} captures the {taken} on {square}.",
                     "references": [f"evidence.json#/positions/{pivot}", f"evidence.json#/moveAssessments/{pivot}"]}
    index = next(i for i, shot in enumerate(drafts) if shot["line"] == "engine-choice")
    chapter = drafts[index]["chapter"]
    for shot in drafts[index:]:
        shot["chapter"] += 1
    drafts.insert(index, dict(chapter=chapter, title=f"The reply on {square}", preset="threat",
                             ply=pivot+1, animate=True, text=text, refs=[key], lead=.2, tail=.55, line="main"))


def opening_question(drafts, editorial, game, selected):
    pivot = selected["deep"]["ply"]
    node = list(game.mainline())[pivot-1]
    piece = piece_name(node.parent.board().piece_at(node.move.from_square))
    drafts[:] = [shot for shot in drafts if shot["text"]]
    drafts[0]["ply"] = pivot-1
    drafts[0]["text"] = f"Where would you put this {piece}? Pick a square, then watch how the game answers."
    editorial["revised"][0]["text"] = drafts[0]["text"]
    editorial["notes"].append("Show the actual decision board and ask for a square before the recorded move.")


def label_narration(output, speech):
    path = output / "publication.json"
    metadata = json.loads(path.read_text())
    metadata["actualVoice"] = speech.voice
    if speech.provider != "pocket":
        credit = "Synthetic narration generated with Kokoro 82M v1.0 (Apache-2.0), using af_heart. https://huggingface.co/hexgrad/Kokoro-82M"
        metadata["description"] = metadata["description"].replace(metadata["voiceCredit"], credit)
        metadata["voiceCredit"] = credit
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
