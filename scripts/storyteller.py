"""Create an evidence-constrained documentary plan and render-ready storyboard."""
import argparse
from array import array
import hashlib
import subprocess
import json
import re
from pathlib import Path

import chess

from chess_intelligence import ROOT, Stockfish, game_from, mover_score, validate
from compile import compile_project
from directors_cut import produce
from story_provider import request_plan

HOOKS = {
    "choice":["What would you do with an offered knight?", "One decision can change the whole attack."],
    "pressure":["The attack starts before the first check.", "Watch how quickly the king loses room."],
    "tempo":["The clock on this attack is measured in moves.", "Watch who gets to ask the next question."],
}
TAKEAWAYS = {
    "replies":["Before you answer a threat, count the replies.", "Start with checks and captures for both sides."],
    "safety":["Before you grab material, check king safety.", "Look at your opponent’s next forcing move."],
    "activity":["Compare the positions after each reply.", "Ask which pieces get to join the attack."],
}
PIECES = {key: chess.piece_name(key) for key in chess.PIECE_TYPES}


def choose(record, override):
    identifier = override or next(iter(record["storyCandidates"]), None)
    selected = next((m for m in record["criticalMoments"] if m["id"] == identifier), None)
    if not selected:
        raise ValueError("No suitable ranked moment or unknown candidate override")
    return selected


def disagreement(screen_loss, deep_loss, agrees):
    return not agrees or abs(screen_loss-deep_loss) >= .15


def verify_deep(record,moment,depth,engine_path):
    screening=record["analysisSettings"]["limit"].get("depth",0)
    if not screening < depth <= 18:
        raise ValueError("Deep verification must exceed the screening depth and stay at or below 18")
    game=game_from(record["game"]["pgn"])
    ply=moment["ply"]
    board=game.board()
    moves=list(game.mainline_moves())
    for move in moves[:ply-1]:
        board.push(move)
    move=moves[ply-1]
    settings=dict(limit={"depth":depth},multiPV=3,pvPlies=8,options={"Threads":1,"Hash":32,"UCI_ShowWDL":True})
    with Stockfish(engine_path,settings,None,120) as engine:
        before=engine.search(board)
        best=before[0]
        played=next((line for line in before if line["moves"][0]["uci"]==move.uci()),None)
        if not played:
            played=engine.search(board,root=move)[0]
        side=board.turn
        board.push(move)
        after=engine.search(board)
        loss=max(0,mover_score(best["evaluation"],side)-mover_score(played["evaluation"],side))
        assessment=record["moveAssessments"][ply-1]
        agrees=best["moves"][0]["uci"]==moment["recommended"]["moves"][0]["uci"]
        return {"engine":engine.identity,"settings":settings,"ply":ply,"best":best,"played":played,
                "after":after[0] if after else None,"estimatedLoss":round(loss,4),
                "screeningLoss":assessment["expectedLoss"],"agreesOnMove":agrees,
                "disagreement":disagreement(assessment["expectedLoss"],loss,agrees)}


def move_words(board,move):
    side="White" if board.turn else "Black"
    piece=PIECES[board.piece_type_at(move.from_square)]
    destination=chess.square_name(move.to_square).upper()
    if board.is_castling(move):
        return f"{side} castles {'short' if board.is_kingside_castling(move) else 'long'}."
    if board.is_capture(move):
        target=PIECES[chess.PAWN if board.is_en_passant(move) else board.piece_type_at(move.to_square)]
        return f"{side}’s {piece} takes the {target} on {destination}."
    return f"{side} moves the {piece} to {destination}."


def catalog(record,deep):
    game=game_from(record["game"]["pgn"])
    selected=deep["ply"]
    available={}
    for ply,node in enumerate(game.mainline(),1):
        if not max(1,selected-2)<=ply<=selected+5:
            continue
        before=node.parent.board()
        move=node.move
        after=node.board()
        phrases=[move_words(before,move)]
        if after.is_checkmate():
            phrases.append("That is checkmate.")
        elif after.is_check():
            phrases.append("The king is in check.")
        if before.is_capture(move) and after.is_check():
            phrases.append("A capture and a check in the same move.")
        if ply==selected and deep["best"]["moves"][0]["uci"]!=move.uci() and deep["estimatedLoss"]>=.06:
            phrases.append("Stockfish scores this reply worse for Black.")
        available[f"ply-{ply}"]={"ply":ply,"san":before.san(move),"phrases":phrases}
    return available


def validate_plan(plan,beats,required):
    if not isinstance(plan,dict) or set(plan)!={"angle","hook","takeaway","beats"}:
        raise ValueError("Plan must contain only angle, hook, takeaway and beats")
    if not all(isinstance(plan[k],str) for k in ("angle","hook","takeaway")):
        raise ValueError("Plan options must be IDs")
    if plan["angle"] not in HOOKS or plan["hook"] not in HOOKS or plan["takeaway"] not in TAKEAWAYS:
        raise ValueError("Unknown story option or unsupported claim")
    selected=plan["beats"]
    if (not isinstance(selected,list) or not 3<=len(selected)<=7 or not all(isinstance(b,str) and b in beats for b in selected)
            or required not in selected):
        raise ValueError("Unknown or missing evidence beat")
    plies=[beats[b]["ply"] for b in selected]
    if plies!=sorted(set(plies)):
        raise ValueError("Recorded moves must be unique and chronological")
    return plan


def draft(record,deep,mode):
    beats=catalog(record,deep)
    required=f"ply-{deep['ply']}"
    if deep["estimatedLoss"]<.06 and deep["best"]["moves"][0]["uci"]!=deep["played"]["moves"][0]["uci"]:
        raise ValueError("Selected mistake does not survive deeper verification")
    if mode=="live":
        proposed,provider=request_plan({"criticalBeat":required,"deepVerification":deep,"beats":beats,
                                       "angles":HOOKS,"hooks":HOOKS,"takeaways":TAKEAWAYS})
    else:
        choices=list(beats)
        proposed={"angle":"choice","hook":"choice","takeaway":"safety",
                  "beats":choices[:7]}
        provider={"mode":"offline-demonstration","model":None}
    return validate_plan(proposed,beats,required),beats,provider


def spoken(text):
    return re.sub(r"\b([A-H])([1-8])\b",lambda m:f"{m[1]} {['','one','two','three','four','five','six','seven','eight'][int(m[2])]}",text)


def direct(record,deep,proposal,beats):
    scenes, ledger=[], []
    def append(ply,title,preset,phrases,support,move=False):
        source=record["moveAssessments"][ply-1]["actual"]["uci"] if ply else ""
        scene=dict(ply=ply,title=title,preset=preset,camera={"focus":source[2:4] or None,"zoom":1.08 if move else 1},
                   lead=.15,tail=.40,transition="glide" if move else "cut",phrases=[[p,.26,spoken(p)] for p in phrases])
        if move:
            scene.update(anchor=0,highlights=[source[:2],source[2:4]],effect="place")
        scenes.append(scene)
        for i,text in enumerate(phrases):
            category,refs=support(i)
            ledger.append({"id":f"claim-{len(ledger)+1}","text":text,"category":category,
                           "references":refs,"status":"editorial" if not refs else "verified",
                           "limitations":["Finite-depth hypothetical line"] if category=="engine-hypothetical" else []})
    tactical_hook={"choice":"One reply can give an attack room to grow.","pressure":"See what changes after the first check.",
                   "tempo":"Watch how the next reply shifts the attack."}
    # Hooks are editorial prompts. Avoid position-specific assertions in the intro.
    context={"choice":"Put yourself on the defending side.","pressure":"Keep an eye on the king’s escape squares.",
             "tempo":"Follow the checks and captures."}
    opening=[tactical_hook[proposal["hook"]],context[proposal["angle"]]]
    append(beats[proposal["beats"][0]]["ply"]-1,"A difficult reply","establishing",opening,lambda _:("editorial",[]))
    for identifier in proposal["beats"]:
        beat=beats[identifier]
        ply=beat["ply"]
        if ply!=scenes[-1]["ply"]+1:
            append(ply-1,"The position ahead","establishing",["Here is the position before the next move."],
                   lambda _:("position",[f"positions/{ply-1}"]))
        def support(index):
            text=beat["phrases"][index]
            if text.startswith("Stockfish"):
                return "engine-comparison",["deepVerification/best","deepVerification/played"]
            return "game",[f"positions/{ply-1}",f"moveAssessments/{ply-1}",f"positions/{ply}"]
        append(ply,"The critical reply" if ply==deep["ply"] else beat["san"],
               "critical" if ply==deep["ply"] else "reveal",beat["phrases"],support,True)
        if ply==deep["ply"] and len(beat["phrases"]) and beat["phrases"][-1].startswith("Stockfish"):
            best=deep["best"]["moves"][0]
            refs=lambda _:("engine-hypothetical",["deepVerification/best/moves/0"])
            append(0,"Engine alternative","variation",["Here is the engine line."],refs)
            scenes[-1]["line"]="engine-choice"
            board=chess.Board(deep["best"]["fen"])
            move=chess.Move.from_uci(best["uci"])
            append(1,"Engine alternative","variation",[move_words(board,move)],refs)
            scenes[-1].update(line="engine-choice",anchor=0,transition="glide",
                              highlights=[best["uci"][:2],best["uci"][2:4]],
                              camera={"focus":best["uci"][2:4],"zoom":1.08})
            append(ply,"Back to the game","establishing",["Now back to the recorded game."],
                   lambda _:("position",[f"positions/{ply}"]))
    append(scenes[-1]["ply"],"The takeaway","final",TAKEAWAYS[proposal["takeaway"]],lambda _:("editorial",[]))
    return scenes, ledger


def prepared_voice(scenes):
    """Use exact Kokoro phrase takes for the default keyless CI demonstration."""
    folder=ROOT/"examples/storyteller"
    manifest=json.loads((folder/"deep-blue-voice.json").read_text())
    asset=folder/"deep-blue-kokoro.mp3"
    if hashlib.sha256(asset.read_bytes()).hexdigest()!=manifest["sha256"]:
        raise ValueError("Prepared Kokoro recording failed checksum verification")
    if any(phrase[2] not in manifest["phrases"] for shot in scenes for phrase in shot["phrases"]):
        raise ValueError("This board plan contains speech absent from the offline voice fixture")
    pcm=array("h",subprocess.check_output(["ffmpeg","-v","error","-i",str(asset),"-f","s16le","-"]))
    def take(text):
        start,count=manifest["phrases"][text]
        return pcm[start:start+count]
    return take


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence",type=Path,default=ROOT/"examples/analysis/deep-blue.json")
    parser.add_argument("--candidate")
    parser.add_argument("--depth",type=int,default=17)
    parser.add_argument("--mode",choices=["offline","live"],default="offline")
    parser.add_argument("--prepared-voice",action="store_true")
    args=parser.parse_args()
    if args.prepared_voice and (args.mode!="offline" or args.candidate):
        parser.error("Prepared voice applies only to the default offline demonstration")
    record=validate(json.loads(args.evidence.read_text()))
    moment=choose(record,args.candidate)
    deep=verify_deep(record,moment,args.depth,ROOT/".cache/stockfish/stockfish")
    proposal,beats,provider=draft(record,deep,args.mode)
    scenes,ledger=direct(record,deep,proposal,beats)
    project=json.loads((ROOT/"projects/legal-mate.json").read_text())
    source=record.get("source")
    sources=[{"label":"Supplied game score","url":source}] if source and source.startswith(("https://","http://")) else []
    if not sources:
        raise ValueError("This documentary requires an attributable game-score link")
    project.update(id="storyteller-documentary",title="Deep Blue · The Critical Reply" if "Deep Blue" in record["game"]["pgn"] else "The Critical Reply",
                   series="The Chess Lab",summary="A Storyteller documentary from verified game evidence.",
                   pgn=record["game"]["pgn"],sources=sources)
    if any(shot.get("line")=="engine-choice" for shot in scenes):
        project["variations"]={"engine-choice":{"fromPly":deep["ply"]-1,"moves":[deep["best"]["moves"][0]["san"]]}}
    synthesis=prepared_voice(scenes) if args.prepared_voice else None
    provider["audioSource"]="prepared-kokoro-takes" if synthesis else "fresh-kokoro-synthesis"
    produce({"scenes":scenes},"kokoro",ROOT/".cache/kokoro","am_michael",.93,project=project,stem="storyteller",synthesis=synthesis)
    storyboard=compile_project(json.loads((ROOT/"projects/storyteller-documentary.json").read_text()))
    runtime=sum(shot["frames"] for shot in storyboard["scenes"])/storyboard["fps"]
    if not 35<=runtime<=60:
        raise ValueError(f"Measured runtime {runtime:.1f}s falls outside 35–60s")
    package=dict(schemaVersion=1,status="storyboard-validated",provider=provider,proposal=proposal,
                 angle={"choice":"The response to the knight","pressure":"King pressure","tempo":"The initiative"}[proposal["angle"]],
                 game={"headers":record["game"]["headers"],"source":source},
                 selection={"id":moment["id"],"score":moment["score"],"reason":"Human override" if args.candidate else "Highest-ranked eligible candidate"},
                 deepVerification=deep,claims=ledger,durationSeconds=runtime,scenes=storyboard["scenes"])
    payload=json.dumps(package,indent=2,ensure_ascii=False)+"\n"
    (ROOT/"out/storyteller-review.json").write_text(payload)
    (ROOT/"src/storyteller-review.generated.json").write_text(payload)
    print(f"Storyteller: {provider['mode']}, {moment['id']}, {runtime:.1f}s, disagreement={deep['disagreement']}")


if __name__=="__main__":
    main()
