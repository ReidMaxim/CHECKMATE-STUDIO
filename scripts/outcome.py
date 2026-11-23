"""Check that a closing script pays off its opening with recorded evidence."""
import io

import chess
import chess.pgn

from compile import StrictGame


class RecordedResult(StrictGame):
    def begin_game(self):
        super().begin_game()
        self.marker = None
        self.header = None

    def visit_header(self, tagname, tagvalue):
        super().visit_header(tagname, tagvalue)
        if tagname == "Result":
            self.header = tagvalue

    def visit_result(self, result):
        if self.marker is not None:
            raise ValueError("Multiple PGN result markers")
        self.marker = result
        super().visit_result(result)


def review_outcome(spec, pgn, nodes, last_shot, evidence):
    visitor = RecordedResult()
    chess.pgn.read_game(io.StringIO(pgn), Visitor=lambda: visitor)
    if visitor.header is not None and visitor.marker is not None and visitor.header != visitor.marker:
        raise ValueError("PGN header and movetext disagree on the result")
    result = visitor.marker
    terminal = nodes[-1].board().outcome()
    if terminal and result not in (None, "*", terminal.result()):
        raise ValueError("Recorded result contradicts the final position")
    if result not in ("1-0", "0-1", "1/2-1/2"):
        result = None
    kind = spec["kind"]
    if kind not in {"recorded-victory", "draw", "local"}:
        raise ValueError("Unsupported resolution scope")
    if (kind == "recorded-victory" and result not in {"1-0", "0-1"}) or (
            kind == "draw" and result != "1/2-1/2"):
        raise ValueError("The ending requires a matching recorded result")
    payoff_refs = spec["payoffRefs"]
    if not spec["question"].strip() or not spec["payoff"].strip() or not payoff_refs or any(
            ref not in evidence or evidence[ref]["ply"] > last_shot for ref in payoff_refs):
        raise ValueError("The opening promise needs a supported local payoff")
    end = nodes[-1]
    evidence["recorded-result"] = {"kind": "game-result", "claim": result, "ply": len(nodes)-1,
                                  "lastMove": end.san() if end.move else None,
                                  "fen": end.board().fen(), "boardTermination": terminal.termination.name if terminal else None}
    result_card = None
    if spec.get("card"):
        if kind == "local":
            raise ValueError("A local lesson cannot request a result card")
        winner = {"1-0": "White", "0-1": "Black"}.get(result)
        headers = nodes[0].headers
        name = headers.get(winner, "?") if winner else None
        title = spec.get("cardLabel", name if name and name != "?" else winner)
        if winner and spec.get("cardLabel") and title not in name.split():
            raise ValueError("Result card label must identify the recorded winner")
        context = [headers.get("Site", "?"), headers.get("Date", "?")[:4]]
        result_card = {"title": f"{title} wins" if winner else "Draw", "score": result,
                       "context": " · ".join(value for value in context if "?" not in value)}
    required = set(payoff_refs)
    if kind != "local":
        required.add("recorded-result")
    for label, option in spec["options"].items():
        refs = option["refs"]
        if (not option["text"].strip() or not required.issubset(refs)
                or any(ref not in evidence or (ref == "recorded-result" and result is None) for ref in refs)):
            raise ValueError(f"Ending {label} does not resolve the opening with verified evidence")
    if spec["selected"] not in spec["options"] or not spec["reason"].strip():
        raise ValueError("An ending and editorial rationale are required")
    return {"question": spec["question"], "payoff": spec["payoff"], "kind": kind,
            "payoffEvidence": {ref: evidence[ref] for ref in payoff_refs},
            "game": evidence["recorded-result"], "lastShownPly": last_shot,
            "gameContinues": last_shot < len(nodes)-1, "card": result_card,
            "selected": spec["selected"], "reason": spec["reason"],
            "options": spec["options"], "proseApproval": "human editorial review"}


def engine_context(executable, nodes, plies):
    """Record the evaluation separately from the PGN result and local payoff."""
    import chess.engine

    positions = []
    depth = 20
    with chess.engine.SimpleEngine.popen_uci(str(executable)) as engine:
        engine.configure({"Threads": 1, "Hash": 64})
        for ply in plies:
            board = nodes[ply].board()
            entries = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=board.legal_moves.count()
                                     if board.is_check() else 1)
            positions.append({"ply": ply, "fen": board.fen(), "lines": [
                {"first": board.san(entry["pv"][0]), "whiteCp": entry["score"].white().score(),
                 "whiteMate": entry["score"].white().mate()} for entry in entries]})
        return {"engine": engine.id["name"], "depth": depth, "positions": positions}
