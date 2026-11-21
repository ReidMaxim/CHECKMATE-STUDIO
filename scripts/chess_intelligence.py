"""Stockfish PGN analysis, reproducible evidence, and a renderer adapter."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time

import chess
import chess.engine
import chess.pgn
from jsonschema import Draft202012Validator, ValidationError

from compile import StrictGame, parse

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs/analysis.schema.json"
VALUES = {1: 1, 2: 3, 3: 3, 4: 5, 5: 9}
WEIGHTS = {"impact": 30, "tactics": 18, "clarity": 14, "surprise": 10,
           "education": 10, "shortLine": 8, "hook": 5, "confidence": 5}
LIMITATIONS = ["Labels and rankings are heuristics, not chess titles or proof of intent.",
               "Finite engine searches and modeled WDL are estimates, not human win probabilities.",
               "PGN headers are supplied metadata and are not independently verified."]


def digest(value):
    return hashlib.sha256(value).hexdigest()


def game_from(pgn):
    parse(pgn)
    return chess.pgn.read_game(io.StringIO(pgn), Visitor=StrictGame)


def line_from(board, moves, kind):
    replay = board.copy(stack=False)
    result = []
    for move in moves:
        if isinstance(move, str):
            move = chess.Move.from_uci(move)
        if move not in replay.legal_moves:
            raise ValueError(f"Illegal {kind} move {move} from {replay.fen()}")
        san = replay.san(move)
        replay.push(move)
        result.append({"san": san, "uci": move.uci(), "fen": replay.fen()})
    return {"kind": kind, "fen": board.fen(), "moves": result}


def normal_score(info):
    score = info["score"].white()
    wdl = info["wdl"].white()
    return {"cp": score.score(), "mate": score.mate(),
            "wdl": [wdl.wins, wdl.draws, wdl.losses], "expectedWhite": wdl.expectation()}


def terminal_score(board):
    winner = board.outcome().winner
    return {"cp": 0 if winner is None else None, "mate": None if winner is None else 0,
            "wdl": [1000, 0, 0] if winner is True else [0, 0, 1000] if winner is False else [0, 1000, 0],
            "expectedWhite": 1 if winner is True else 0 if winner is False else .5}


class Stockfish:
    def __init__(self, executable, settings, cache, budget):
        self.executable = executable
        self.settings = settings
        self.cache = cache
        self.deadline = time.monotonic() + budget
        self.hits = self.searches = 0

    def __enter__(self):
        self.engine = chess.engine.SimpleEngine.popen_uci(str(self.executable), timeout=12)
        try:
            self.identity = dict(self.engine.id, binarySha256=digest(self.executable.read_bytes()),
                                 nnue={key: self.engine.options[key].default for key in self.engine.options
                                       if key.startswith("EvalFile")})
            if not self.identity["name"].startswith("Stockfish 17.1"):
                raise ValueError(f"Expected Stockfish 17.1, received {self.identity['name']}")
            self.engine.configure(self.settings["options"])
        except BaseException:
            self.engine.close()
            raise
        return self

    def __exit__(self, *_):
        self.engine.close()

    def search(self, board, root=None):
        if time.monotonic() >= self.deadline:
            raise TimeoutError("Total analysis budget exhausted")
        if board.is_game_over():
            return []
        limit = self.settings["limit"]
        count = 1 if root else self.settings["multiPV"]
        root_uci = root.uci() if root else None
        # Stockfish can account for repetition. Include full root position and move history.
        key = digest(json.dumps([1, self.identity, self.settings, board.root().fen(),
                                 [move.uci() for move in board.move_stack], root_uci], sort_keys=True).encode())
        target = self.cache / f"{key}.json" if self.cache else None
        if target and target.is_file():
            cached = json.loads(target.read_text())
            for item in cached:
                if item["fen"] != board.fen() or line_from(board, [m["uci"] for m in item["moves"]], item["kind"])["moves"] != item["moves"]:
                    raise ValueError("Cached variation failed replay validation")
            self.hits += 1
            return cached
        self.searches += 1
        infos = self.engine.analyse(board, chess.engine.Limit(**limit), multipv=count,
                                    root_moves=[root] if root else None, game=object())
        evidence = []
        for info in infos:
            variation = line_from(board, info["pv"][:self.settings["pvPlies"]], "engine-root" if root else "engine")
            variation.update(rank=info.get("multipv", 1), evaluation=normal_score(info),
                             depth=info["depth"], nodes=info.get("nodes"), seconds=info.get("time"))
            evidence.append(variation)
        if not evidence:
            raise ValueError("Stockfish supplied no principal variation for a nonterminal position")
        if target:
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", dir=target.parent, delete=False) as temp:
                json.dump(evidence, temp)
            Path(temp.name).replace(target)
        return evidence


def mover_score(evaluation, turn):
    white = evaluation["expectedWhite"]
    return white if turn else 1 - white


def classification(legal, played, best, loss, before, after, keeps_mate=True):
    if legal == 1:
        return "forced"
    if played == best:
        return "best"
    if not keeps_mate and loss < .04:
        return "inaccuracy"
    # Require both outcome deterioration and a meaningful destination for large labels.
    if loss >= .26 and (after < .40 or before >= .67 > after):
        return "blunder"
    if loss >= .13:
        return "mistake"
    if loss >= .06:
        return "inaccuracy"
    return "near-best" if loss <= .02 else "good"


def balance(board, turn):
    return sum(v * (len(board.pieces(p, turn))-len(board.pieces(p, not turn)))
               for p, v in VALUES.items())


def detect(board, after, move, assessment, recommended, played_line):
    if assessment["quality"] == "forced":
        return None
    before = assessment["bestExpectedMover"]
    played = assessment["playedExpectedMover"]
    loss = assessment["expectedLoss"]
    observed = line_from(board, [move], "game")
    ending = chess.Board(played_line["moves"][-1]["fen"]) if played_line["moves"] else after
    sacrifice = balance(board, board.turn) - balance(ending, board.turn) >= 2 and played >= .60 and loss <= .06 and not after.is_checkmate()
    opponent_mates = assessment["after"]["mate"] not in (None, 0) and mover_score(assessment["after"], board.turn) == 0
    endgame = len(board.piece_map()) <= 7 and loss >= .10
    is_tactical = board.is_capture(move) or after.is_check()
    if opponent_mates and mover_score(assessment["before"], board.turn) > .10:
        category, summary = "allows-mate", "The played move allows a Stockfish-reported mate for the opponent."
    elif endgame:
        category, summary = "endgame-turn", "This move changes the modeled outcome in a position with seven pieces or fewer."
    elif assessment["quality"] == "blunder":
        category, summary = "major-blunder", "The played move gives up a substantial share of the mover’s modeled expected result."
    elif loss >= .14 and before >= .64:
        category, summary = "missed-opportunity", "Stockfish found a stronger alternative from the same position."
    elif after.is_checkmate() or (is_tactical and assessment["after"]["mate"] is not None and
                                    mover_score(assessment["after"], board.turn) == 1 and loss <= .05):
        category, summary = "mating-sequence", "The played move delivers or continues a mating sequence."
    elif sacrifice:
        category, summary = "sacrifice-candidate", "A short engine line gives up material while preserving a favorable evaluation. Intent is unknown."
    elif loss >= .16:
        category, summary = "evaluation-reversal", "The played move causes a sizable modeled outcome shift."
    elif is_tactical and played >= .66 and len(played_line["moves"]) <= 6 and loss <= .03:
        category, summary = "tactical-combination", "The played check or capture retains a favorable engine evaluation."
    else:
        return None
    breakdown = {"impact": min(1, loss / .30), "tactics": 1 if is_tactical or opponent_mates else .35,
                 "clarity": 1 if after.is_checkmate() or opponent_mates else .65,
                 "surprise": 1 if sacrifice or opponent_mates else min(1, loss / .25),
                 "education": 1 if endgame or opponent_mates else .65,
                 "shortLine": 1 if len(played_line["moves"]) <= 5 else .5,
                 "hook": .9 if sacrifice or opponent_mates else .65,
                 "confidence": min(1, recommended["depth"] / 16)}
    return {"category": category, "summary": summary, "dimensions": breakdown,
            "beforeFen": board.fen(), "afterFen": after.fen(), "actual": observed,
            "recommended": recommended, "playedContinuation": played_line,
            "before": assessment["before"], "after": assessment["after"],
            "focus": [move.uci()[:2], move.uci()[2:4]], "limitations": LIMITATIONS[:2]}


def rank_moments(moments, minimum):
    chosen = []
    for moment in sorted(moments, key=lambda item: (-item["score"], item["ply"])):
        if moment["score"] >= minimum and all(abs(moment["ply"]-other["ply"]) > 2 for other in chosen):
            chosen.append(moment)
        if len(chosen) == 3:
            break
    return [item["id"] for item in chosen]


def analyze(pgn, engine, weights=WEIGHTS, minimum=47):
    began = time.monotonic()
    game = game_from(pgn)
    board = game.board()
    moves = list(game.mainline_moves())
    if len(moves) > 600:
        raise ValueError("PGN exceeds the 600-ply budget")
    positions, assessments, moments = [], [], []

    def get_position(state):
        variation = engine.search(state)
        return {"fen": state.fen(), "turn": "white" if state.turn else "black",
                "evaluation": variation[0]["evaluation"] if variation else terminal_score(state), "lines": variation}

    current = get_position(board)
    positions.append(current)
    for ply, move in enumerate(moves, 1):
        if not current["lines"]:
            raise ValueError(f"PGN continues past a terminal position at ply {ply}")
        preferred = current["lines"][0]
        played_line = next((line for line in current["lines"] if line["moves"][0]["uci"] == move.uci()), None)
        if played_line is None:
            played_line = engine.search(board, root=move)[0]
        actual = line_from(board, [move], "game")["moves"][0]
        previous = board.copy()
        board.push(move)
        following = get_position(board)
        best_expected = mover_score(preferred["evaluation"], previous.turn)
        played_expected = mover_score(played_line["evaluation"], previous.turn)
        if board.is_game_over():
            played_expected = mover_score(following["evaluation"], previous.turn)
        loss = round(max(0, best_expected - played_expected), 4)
        best_mate = preferred["evaluation"]["mate"]
        played_mate = played_line["evaluation"]["mate"]
        keeps_mate = best_mate is None or best_expected != 1 or played_mate is not None or board.is_checkmate()
        assessment = {"ply": ply, "player": current["turn"], "moveNumber": previous.fullmove_number,
                      "actual": actual, "bestMove": preferred["moves"][0], "before": current["evaluation"],
                      "after": following["evaluation"], "bestExpectedMover": best_expected,
                      "playedExpectedMover": played_expected, "expectedLoss": loss,
                      "expectedChangeMover": round(mover_score(following["evaluation"], previous.turn) - best_expected, 4),
                      "quality": classification(previous.legal_moves.count(), move.uci(), preferred["moves"][0]["uci"],
                                                loss, best_expected, played_expected, keeps_mate),
                      "playedLine": played_line}
        moment = detect(previous, board, move, assessment, preferred, played_line)
        if moment:
            score = round(sum(moment["dimensions"][name]*weight for name, weight in weights.items()) / sum(weights.values()) * 100, 1)
            moments.append(dict(moment, id=f"ply-{ply}", ply=ply, score=score, move=actual["san"],
                                evidence={"beforePosition":ply-1,"afterPosition":ply,"assessmentPly":ply}))
        positions.append(following)
        assessments.append(assessment)
        current = following
    seconds = time.monotonic()-began
    candidates = rank_moments(moments, minimum)
    return {"schemaVersion": 1, "game": {"headers": {k:v for k,v in game.headers.items() if v not in ("?", "????.??.??")},
                                         "pgn": pgn, "sha256": digest(pgn.encode())},
            "source": game.headers.get("Source"), "engine": engine.identity,
            "analysisSettings": dict(engine.settings, perspective="White", weights=weights, minimumStoryScore=minimum),
            "positions": positions, "moveAssessments": assessments, "criticalMoments": moments,
            "storyCandidates": candidates, "warnings": LIMITATIONS,
            "performance": {"positions":len(positions),"engineSearches":engine.searches,"cacheHits":engine.hits,
                            "seconds":round(seconds,4),"secondsPerPosition":round(seconds/len(positions),4),
                            "candidateCount":len(candidates)}}


def validate(record):
    Draft202012Validator(json.loads(SCHEMA.read_text())).validate(record)
    game = game_from(record["game"]["pgn"])
    if record["game"]["sha256"] != digest(record["game"]["pgn"].encode()):
        raise ValueError("PGN digest disagrees with stored input")
    board = game.board()
    rows = record["positions"]
    assessments = record["moveAssessments"]
    moves = list(game.mainline_moves())
    if len(rows) != len(moves)+1 or len(assessments) != len(moves):
        raise ValueError("PGN and analysis disagree on game length")

    def check_score(score):
        win, draw, loss = score["wdl"]
        if win+draw+loss != 1000 or abs(score["expectedWhite"]-(win+.5*draw)/1000) > 1e-8:
            raise ValueError("WDL and expected score disagree")

    def check_line(line):
        check_score(line["evaluation"])
        actual = line_from(chess.Board(line["fen"]), [m["uci"] for m in line["moves"]], line["kind"])
        if actual["moves"] != line["moves"]:
            raise ValueError("Variation SAN or FEN disagrees with legal replay")

    for index, row in enumerate(rows):
        if row["fen"] != board.fen() or row["turn"] != ("white" if board.turn else "black"):
            raise ValueError("Position FEN or side disagrees with PGN")
        check_score(row["evaluation"])
        for variation in row["lines"]:
            if variation["fen"] != row["fen"]:
                raise ValueError("Variation starts from a different position")
            check_line(variation)
        if row["lines"] and row["lines"][0]["evaluation"] != row["evaluation"]:
            raise ValueError("Position evaluation disagrees with its principal variation")
        if index == len(moves):
            break
        item = assessments[index]
        if not row["lines"]:
            raise ValueError("Missing position analysis before a played move")
        next_board = board.copy()
        next_board.push(moves[index])
        played_evaluation = rows[index+1]["evaluation"] if next_board.is_game_over() else item["playedLine"]["evaluation"]
        if (item["ply"] != index+1 or item["player"] != row["turn"] or
                item["before"] != row["evaluation"] or item["after"] != rows[index+1]["evaluation"] or
                item["actual"] != line_from(board, [moves[index]], "game")["moves"][0] or
                item["bestMove"] != row["lines"][0]["moves"][0] or
                item["playedLine"]["fen"] != row["fen"] or item["playedLine"]["moves"][0]["uci"] != moves[index].uci() or
                item["bestExpectedMover"] != mover_score(row["evaluation"], board.turn) or
                item["playedExpectedMover"] != mover_score(played_evaluation, board.turn) or
                item["expectedChangeMover"] != round(mover_score(rows[index+1]["evaluation"], board.turn)-item["bestExpectedMover"],4) or
                item["expectedLoss"] != round(max(0, item["bestExpectedMover"] - item["playedExpectedMover"]), 4)):
            raise ValueError("Move assessment disagrees with PGN or evaluations")
        check_line(item["playedLine"])
        board.push(moves[index])
    ids = {m["id"] for m in record["criticalMoments"]}
    if len(ids) != len(record["criticalMoments"]):
        raise ValueError("Duplicate critical moment IDs")
    for moment in record["criticalMoments"]:
        ply = moment["ply"]
        if not 1 <= ply <= len(moves):
            raise ValueError("Moment ply outside game")
        item = assessments[ply-1]
        if (moment["actual"]["moves"] != [item["actual"]] or moment["beforeFen"] != rows[ply-1]["fen"] or
                moment["afterFen"] != rows[ply]["fen"] or moment["actual"]["fen"] != moment["beforeFen"] or
                moment["recommended"] != rows[ply-1]["lines"][0] or moment["playedContinuation"] != item["playedLine"] or
                moment["before"] != item["before"] or moment["after"] != item["after"]):
            raise ValueError("Moment evidence disagrees with assessment")
    if record["storyCandidates"] != rank_moments(record["criticalMoments"], record["analysisSettings"]["minimumStoryScore"]):
        raise ValueError("Story candidates disagree with ranked evidence")
    return record


def storyboard_input(record, candidate):
    validate(record)
    moment = next((m for m in record["criticalMoments"] if m["id"] == candidate), None)
    if moment is None:
        raise ValueError(f"Unknown moment: {candidate}")
    recommended = moment["recommended"]
    return {"pgn": record["game"]["pgn"],
            "variations": {"engine-alternative": {"fromPly":moment["ply"]-1,
                                                "moves":[move["san"] for move in recommended["moves"]]}},
            "focus": moment["focus"], "playedPly":moment["ply"], "lineKind":"engine"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True, dest="command")
    check = commands.add_parser("validate")
    check.add_argument("evidence", type=Path)
    adapter = commands.add_parser("storyboard")
    adapter.add_argument("evidence", type=Path)
    adapter.add_argument("candidate")
    run = commands.add_parser("analyze")
    run.add_argument("pgn", type=Path)
    run.add_argument("--engine", type=Path, default=ROOT/".cache/stockfish/stockfish")
    run.add_argument("--output", type=Path, required=True)
    limits = run.add_mutually_exclusive_group()
    limits.add_argument("--depth", type=int)
    limits.add_argument("--time", type=float)
    run.add_argument("--multipv", type=int, default=3)
    run.add_argument("--budget", type=float, default=180)
    run.add_argument("--cache", type=Path)
    run.add_argument("--weights", type=Path)
    run.add_argument("--minimum", type=float, default=47)
    args = parser.parse_args()
    if args.command == "validate":
        validate(json.loads(args.evidence.read_text()))
        return
    if args.command == "storyboard":
        print(json.dumps(storyboard_input(json.loads(args.evidence.read_text()), args.candidate), indent=2))
        return
    if not 1 <= args.multipv <= 5 or not 1 <= args.budget <= 900 or not 0 <= args.minimum <= 100:
        parser.error("MultiPV must be 1–5, budget 1–900 seconds and minimum 0–100")
    limit = {"time":args.time} if args.time is not None else {"depth":args.depth if args.depth is not None else 12}
    if not (.02 <= limit.get("time",1) <= 2 and 1 <= limit.get("depth",1) <= 20):
        parser.error("Depth must be 1–20 or time .02–2 seconds per search")
    weights = json.loads(args.weights.read_text()) if args.weights else WEIGHTS
    if set(weights) != set(WEIGHTS) or not all(isinstance(w,(int,float)) and 0 <= w <= 100 for w in weights.values()) or not sum(weights.values()):
        parser.error("Weights must match the documented dimensions and sum to a positive value")
    settings = {"limit":limit,"multiPV":args.multipv,"pvPlies":8,
                "options":{"Threads":1,"Hash":32,"UCI_ShowWDL":True}}
    pgn = args.pgn.read_text(encoding="utf-8-sig")
    game_from(pgn)
    with Stockfish(args.engine, settings, args.cache, args.budget) as engine:
        analysis = validate(analyze(pgn, engine, weights, args.minimum))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(analysis, ensure_ascii=False, separators=(",",":"))+"\n")
    print(json.dumps(analysis["performance"]))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, TimeoutError, chess.engine.EngineError, ValidationError) as error:
        sys.exit(f"Analysis failed: {error}")
