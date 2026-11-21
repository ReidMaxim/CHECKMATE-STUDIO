import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

import chess
import chess.engine
from jsonschema.exceptions import ValidationError

from chess_intelligence import (ROOT, Stockfish, analyze, classification, game_from,
                                line_from, mover_score, normal_score, rank_moments,
                                storyboard_input, terminal_score, validate)
from compile import compile_project

SETTINGS = {"limit":{"depth":12},"multiPV":3,"pvPlies":8,
            "options":{"Threads":1,"Hash":32,"UCI_ShowWDL":True}}


def fixture(name):
    return (ROOT / f"examples/chess/{name}.pgn").read_text()


class EvidenceTests(unittest.TestCase):
    def test_pgn_and_illegal_moves(self):
        self.assertEqual(game_from(fixture("pawn-ending")).board().king(chess.WHITE),chess.E6)
        with self.assertRaises(ValueError):
            game_from("1. e4 e5 2. e6")
        with self.assertRaises(ValueError):
            line_from(chess.Board(), ["e2e5"], "engine")

    def test_black_pov_and_mate(self):
        evaluation = normal_score({"score":chess.engine.PovScore(chess.engine.Mate(3),chess.BLACK),
            "wdl":chess.engine.PovWdl(chess.engine.Wdl(1000,0,0),chess.BLACK)})
        self.assertEqual(evaluation["mate"], -3)
        self.assertIsNone(evaluation["cp"])
        self.assertEqual(mover_score(evaluation, chess.BLACK), 1)
        self.assertEqual(mover_score(evaluation, chess.WHITE), 0)
        mate = game_from(fixture("legal-mate")).end().board()
        self.assertEqual(terminal_score(mate)["wdl"], [1000,0,0])

    def test_labels_and_rank_suppression(self):
        self.assertEqual(classification(1,"a","b",.5,.8,.3),"forced")
        self.assertEqual(classification(4,"a","b",.55,1,.45),"blunder")
        self.assertEqual(classification(4,"a","b",.01,1,.99),"near-best")
        moments=[{"id":str(i),"ply":i,"score":value} for i,value in [(2,95),(1,95),(4,70),(9,65),(31,20)]]
        self.assertEqual(rank_moments(moments,47),["1","4","9"])
        self.assertEqual(rank_moments(moments,100),[])

    def test_schema_semantics_and_renderer_adapter(self):
        data=validate(json.loads((ROOT/"examples/analysis/legal-mate.json").read_text()))
        wrong_version=dict(data,schemaVersion=2)
        with self.assertRaises(ValidationError):
            validate(wrong_version)
        broken=copy.deepcopy(data)
        broken["positions"][0]["lines"][0]["moves"][0]["uci"]="e2e5"
        with self.assertRaisesRegex(ValueError,"Illegal engine"):
            validate(broken)
        fragment=storyboard_input(data, data["storyCandidates"][0])
        project={"pgn":fragment["pgn"],"variations":fragment["variations"],"scenes":[],"audio":[]}
        result=compile_project(project)
        self.assertGreater(len(result["lines"]["engine-alternative"]),1)

    def test_budget_expires_before_search(self):
        stockfish=Stockfish(Path("unused"),SETTINGS,None,-1)
        with self.assertRaisesRegex(TimeoutError,"budget"):
            stockfish.search(chess.Board())

    def test_engine_crash_during_handshake(self):
        with self.assertRaises(chess.engine.EngineTerminatedError):
            with Stockfish(Path("/bin/false"),SETTINGS,None,3):
                self.fail("Invalid engine cannot start")


@unittest.skipUnless(os.getenv("STOCKFISH_INTEGRATION")=="1","enable real Stockfish integration")
class IntegrationTests(unittest.TestCase):
    binary=ROOT/".cache/stockfish/stockfish"

    def run_game(self,pgn,cache=None):
        with Stockfish(self.binary,SETTINGS,cache,15) as engine:
            return validate(analyze(pgn,engine))

    def test_real_black_blunder_and_white_endgame(self):
        example=self.run_game(fixture("deep-blue"))
        choice=example["moveAssessments"][15]
        self.assertEqual((choice["player"],choice["actual"]["san"],choice["quality"]),("black","Qe7","blunder"))
        self.assertGreater(choice["after"]["expectedWhite"],choice["before"]["expectedWhite"])
        white=self.run_game(fixture("pawn-ending"))
        move=white["moveAssessments"][0]
        self.assertGreater(move["expectedLoss"],.30)
        self.assertGreater(move["before"]["expectedWhite"],move["after"]["expectedWhite"])
        self.assertEqual(white["criticalMoments"][0]["category"],"endgame-turn")

    def test_repeatability_cache_and_misleading_check(self):
        with tempfile.TemporaryDirectory() as folder:
            cache=Path(folder)
            runs=[self.run_game(fixture("quiet-ending"), path) for path in (None,cache,cache)]
        for result in runs:
            self.assertEqual(result["storyCandidates"],[])
            self.assertTrue(result["moveAssessments"][0]["actual"]["san"].endswith("+"))
        self.assertEqual(runs[-1]["performance"]["engineSearches"],0)
        self.assertGreater(runs[-1]["performance"]["cacheHits"],0)
        for result in runs:
            for row in result["positions"]:
                for line in row["lines"]:
                    line.pop("seconds")
            result["moveAssessments"][0]["playedLine"].pop("seconds", None)
        self.assertEqual(runs[0]["positions"],runs[-1]["positions"])
        self.assertEqual(runs[0]["moveAssessments"],runs[-1]["moveAssessments"])

    def test_forced_defense_and_actual_mate(self):
        game=self.run_game(fixture("legal-mate"))
        self.assertEqual(game["moveAssessments"][11]["quality"],"forced")
        self.assertEqual(game["positions"][-1]["evaluation"]["mate"],0)
        self.assertFalse(any(m["ply"]==12 for m in game["criticalMoments"]))
        self.assertTrue(any(m["category"]=="mating-sequence" for m in game["criticalMoments"]))
