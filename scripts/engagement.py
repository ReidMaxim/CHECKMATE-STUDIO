"""Build position-specific editorial options from verified game replay."""
import chess

from commentary_pass import forced_clearance, piece_name


def design(nodes, selected, angle, *, suppress=False):
    pivot = selected["deep"]["ply"]
    node = nodes[pivot - 1]
    board = node.parent.board()
    candidates = []

    def add(kind, text, position, placement, action, evidence, reason, downside):
        candidates.append(dict(type=kind, wording=text, fen=position.fen(), placement=placement,
                               action=action, evidence=evidence, reason=reason, downside=downside))

    if not suppress:
        motif = forced_clearance(nodes, pivot)
        if motif:
            start = nodes[pivot-3].parent.board()
            add("prediction", f"How would you move the {piece_name(motif['responder'])} out of the way?",
                start, "opening", "Predict a way to clear the route", [f"positions/{pivot-3}"],
                "The blocker is visible before the forcing sequence.", "Some viewers need time to scan the board.")
            add("recognition", "Which piece cleared the mating route?", node.board(), "pinned-comment",
                "Identify the blocker", [f"positions/{pivot-2}", f"positions/{pivot}"],
                "The answer is demonstrated by the recorded moves.", "Repeats the payoff if spoken.")
        if angle == "decision-contrast":
            best = chess.Move.from_uci(selected["deep"]["best"]["moves"][0]["uci"])
            if best in board.legal_moves and best != node.move:
                played, alternative = board.san(node.move), board.san(best)
                piece = piece_name(board.piece_at(node.move.from_square))
                wording = f"What would you play here? Compare {played} (played) and {alternative} (Stockfish)."
                add("choice", wording, board, "pinned-comment", "Compare two legal moves from the same board",
                    [f"moveAssessments/{pivot-1}", "selected/deep/best"],
                    f"The film shows the recorded move and engine alternative. Focus on the {piece}.",
                    "Notation may be unfamiliar to beginners.")
        if angle == "positional-lesson" and board.is_valid() and not board.is_game_over() and len(board.piece_map()) <= 12:
            add("reflection", "What would you check before committing to a move in this endgame?", board,
                "pinned-comment", "Explain an endgame decision habit", [f"positions/{pivot-1}"],
                "The viewer can inspect a concrete endgame.", "Keep the question out of the narration if the ending lands.")
    return {"candidates": candidates[:3], "selected": candidates[0] if candidates else
            {"type": "none", "reason": "No supported interaction adds enough to the story."}}
