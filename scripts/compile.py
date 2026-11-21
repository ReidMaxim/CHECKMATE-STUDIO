"""Compile author-supplied PGN to verified board snapshots for the renderer."""
import io
import json
import re
import sys
from pathlib import Path

import chess
import chess.pgn

ROOT = Path(__file__).resolve().parents[1]


class StrictGame(chess.pgn.GameBuilder):
    def handle_error(self, error):
        raise ValueError(str(error))


def position(fen):
    if len(fen.split()) != 6:
        raise ValueError("FEN must contain six fields")
    board = chess.Board(fen)
    if not board.is_valid():
        raise ValueError(f"Invalid chess position (status {board.status()})")
    return board


def snapshot(board):
    return dict(fen=board.fen(), pieces={chess.square_name(s): p.symbol()
                                        for s, p in board.piece_map().items()},
                check=chess.square_name(board.king(board.turn)) if board.is_check() else None,
                mate=board.is_checkmate(), legal=board.legal_moves.count())


def parse(pgn, fen=None):
    if fen is not None:
        position(fen)
    if not pgn.strip():
        return [snapshot(position(fen)) if fen else snapshot(chess.Board())]
    body = re.sub(r'^\s*\[[^\n]*\]\s*$', '', pgn, flags=re.M)
    body = re.sub(r'\{[^}]*\}|;[^\n]*|^%[^\n]*', ' ', body, flags=re.M)
    allowed_gaps = r'(?:\s|\d+\.{1,3}|\.{1,3}|[+#])*'
    cursor = 0
    for token in chess.pgn.MOVETEXT_REGEX.finditer(body):
        if not re.fullmatch(allowed_gaps, body[cursor:token.start()]):
            raise ValueError(f"Unrecognized PGN text: {body[cursor:token.start()].strip()}")
        cursor = token.end()
    if not re.fullmatch(allowed_gaps, body[cursor:]):
        raise ValueError(f"Unrecognized PGN text: {body[cursor:].strip()}")
    stream = io.StringIO(pgn)
    game = chess.pgn.read_game(stream, Visitor=StrictGame)
    if game is None or chess.pgn.read_game(stream) is not None:
        raise ValueError("Expected exactly one PGN game")
    board = game.board()
    if type(board) is not chess.Board or board.chess960 or not board.is_valid():
        raise ValueError("Expected a valid standard chess position")
    if fen is not None and board.fen() != position(fen).fen():
        raise ValueError("Starting FEN disagrees with PGN")
    frames = [snapshot(board)]
    for move in game.mainline_moves():
        if move not in board.legal_moves:
            raise ValueError(f"Illegal PGN move: {move}")
        source, target = map(chess.square_name, (move.from_square, move.to_square))
        capture = chess.square_name(move.to_square + (-8 if board.turn else 8)) if board.is_en_passant(move) else target if board.is_capture(move) else None
        rook = None
        if board.is_castling(move):
            kingside = board.is_kingside_castling(move)
            rook = [(("h" if kingside else "a") + source[1]), (("f" if kingside else "d") + source[1])]
        san = board.san(move)
        board.push(move)
        frames.append(dict(snapshot(board), move=dict(source=source, target=target, capture=capture, rook=rook, san=san)))
    if len(frames) == 1 and not game.headers.get("FEN"):
        raise ValueError("PGN contains no recognized moves")
    return frames


def compile_project(project, assets=ROOT / "public"):
    primary = parse(project["pgn"], project.get("fen"))
    lines = {"main": primary}
    for name, line in project.get("variations", {}).items():
        origin = line["fromPly"]
        if not 0 <= origin < len(primary):
            raise ValueError(f"{name}: variation origin out of range")
        board = chess.Board(primary[origin]["fen"])
        frames = [snapshot(board)]
        for san in line["moves"]:
            move = board.parse_san(san)
            game = chess.pgn.Game()
            game.setup(board)
            game.add_variation(move)
            next_frame = parse(str(game))[1]
            board.push(move)
            frames.append(next_frame)
        lines[name] = frames
    previous = None
    for index, scene in enumerate(project["scenes"], 1):
        line = scene.get("line", "main")
        ply = scene["ply"]
        if line not in lines or not 0 <= ply < len(lines[line]):
            raise ValueError(f"Scene {index}: position index out of range")
        current = (line, ply)
        if scene["moveFrames"] and (previous != (line, ply - 1) or ply == 0):
            raise ValueError(f"Scene {index}: animated move must advance one ply from the preceding scene")
        if previous is not None and previous != current and not scene["moveFrames"] and scene["transition"] != "cut":
            raise ValueError(f"Scene {index}: changing position without animation requires a cut")
        previous = current
    for track in project["audio"]:
        asset = track["asset"]
        if not re.fullmatch(r"[a-zA-Z0-9_-]+\.(mp3|wav|m4a)", asset) or not (assets / asset).is_file():
            raise ValueError(f"Missing or unsupported audio asset: {asset}")
    return dict(project, lines=lines)


if __name__ == "__main__":
    try:
        projects = [compile_project(json.loads(file.read_text())) for file in sorted((ROOT / "projects").glob("*.json"))]
        (ROOT / "src/generated.json").write_text(json.dumps(projects, ensure_ascii=False))
        print(f"Compiled {len(projects)} chess storyboard(s)")
    except (ValueError, KeyError, IndexError) as exc:
        sys.exit(f"Storyboard chess validation failed: {exc}")
