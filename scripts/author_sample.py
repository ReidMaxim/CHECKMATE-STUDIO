"""Authoring helper for the committed sample storyboard."""
import json
from pathlib import Path

scenes = []
def shot(preset, title, seconds, ply, lines, *, focus=None, marks=(), arrows=(), zoom=1, transition="cut"):
    captions = [{"from": a * 30, "to": b * 30, "text": line} for a, b, line in lines]
    scenes.append(dict(preset=preset, title=title, frames=seconds * 30, ply=ply,
                       moveFrames=min(24, seconds * 30 - 1) if scenes and scenes[-1]["ply"] + 1 == ply else 0,
                       camera=dict(focus=focus, zoom=zoom), highlights=marks, arrows=arrows,
                       transition=transition, captions=captions))

shot("establishing", "A queen for a king", 6, 8, [
    (0, 3, "Would you let someone take your queen?"),
    (3, 6, "White is about to leave it hanging on purpose.")], marks=["d1","g4"])
shot("threat", "Follow the diagonal", 7, 8, [
    (0, 3, "Black’s bishop is staring down the knight."),
    (3, 7, "If the knight moves, the queen is exposed.")],
    focus="e2", zoom=1.13, marks=["f3","d1"], arrows=[["g4","d1"]], transition="glide")
shot("critical", "The knight moves", 5, 9, [
    (0, 5, "White takes on e5 anyway. The queen is wide open.")],
    focus="e4", zoom=1.08, marks=["e5","d1"], transition="glide")
shot("suspense", "Black takes the bait", 5, 10, [
    (0, 5, "Black takes the queen. Now watch the white bishop.")],
    marks=["d1","c4"], transition="glide")
shot("reveal", "Check on f7", 5, 11, [
    (0, 5, "Bishop takes f7, with check. The knight on e5 protects it.")],
    marks=["f7","e5"], arrows=[["e5","f7"]])
shot("reveal", "The king steps out", 4, 12, [
    (0, 4, "The king has one legal reply: step to e7.")],
    marks=["e7"])
shot("final", "Two knights. One mate.", 9, 13, [
    (0, 4, "The other knight jumps to d5. Checkmate."),
    (4, 9, "Before you grab the queen, look at the checks you’re giving away.")],
    marks=["d5","e7"], arrows=[["d5","e7"]])
project = dict(
    version=1, id="legal-mate", title="A queen for a king", series="Chess Crimes",
    summary="A bishop takes the queen. Two knights and a bishop finish the game.",
    sources=[dict(label="Edward Winter, Chess Notes 5720 · published variant with 4…g6",
                  url="https://www.chesshistory.com/winter/winter49.html#5720._Legall_game")],
    pgn=Path("projects/legal-mate.pgn").read_text(), orientation="white", theme="forest",
    width=1080, height=1920, fps=30, audio=[dict(asset="legal-narration.mp3", start=0, volume=0.92, kind="narration", label="Synthetic test narration · Flite")],
    scenes=scenes)
Path("projects/legal-mate.json").write_text(json.dumps(project, ensure_ascii=False, indent=2)+"\n")
