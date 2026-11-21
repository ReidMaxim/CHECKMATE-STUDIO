"""Editorial treatments and phrase direction for a verified game."""
from copy import deepcopy

RUBRIC = {"clarity":25,"originality":15,"support":25,"accessibility":15,"structure":10,"visuals":10}
TREATMENTS = {
    "choice": dict(title="The Price of Waiting",hook="The knight is already on the table.",
                   arc="offer → delayed capture → exposed king", audience="casual chess viewers",
                   visuals="Hold on e6, contrast the two replies, then follow the check.",
                   risks="Explain engine preference without calling it a forced result.",
                   scores=[5,4,5,5,5,5]),
    "pressure": dict(title="One Move Ahead", hook="Keep your eye on the king.",
                     arc="pressure → check → retreat", audience="beginners learning forcing moves",
                     visuals="Track the bishop’s check and the king’s retreat.",
                     risks="Keep the segment short enough to explain the alternative.",
                     scores=[5,4,5,5,4,4]),
    "tempo": dict(title="Two Ways to Take a Knight",hook="Play the two replies side by side.",
                  arc="question → comparison → consequence",audience="players familiar with analysis",
                  visuals="Show a labeled alternative from the exact branch position.",
                  risks="Clearly distinguish the hypothetical reply from the game.",
                  scores=[4,5,5,4,4,5]),
}


def treatments(deep):
    result={}
    for key,option in TREATMENTS.items():
        scores=dict(zip(RUBRIC,option["scores"],strict=True))
        result[key]={**option,"scores":scores,"runtimeSeconds":[35,60],
                     "moment":f"ply-{deep['ply']}",
                     "essentialClaims":["deepVerification/played","deepVerification/best"],
                     "score":sum(scores[k]*weight/5 for k,weight in RUBRIC.items())}
    return result


def choose_treatment(options, override=None):
    return override or max(options,key=lambda key:options[key]["score"])


def shape_scenes(scenes,ledger,deep,record,treatment,spoken,*,authored_demo=True):
    """Change cadence, framing and evidence order without editing PGN."""
    scenes=deepcopy(scenes)
    claims=deepcopy(ledger)
    # This authored evidence treatment is conditional on the exact recorded and engine moves.
    actual=[r["actual"]["san"] for r in record["moveAssessments"]]
    if authored_demo and deep["ply"]==16 and actual[14:20]==["Nxe6","Qe7","O-O","fxe6","Bg6+","Kd8"] and deep["best"]["moves"][0]["san"]=="fxe6":
        specs=[
          (14,"A knight on offer","establishing",[
              ("Look at the pawn on E6.",["positions/14"]),
              ("Deep Blue is about to offer a knight for it.",["moveAssessments/14","moveAssessments/17"])]),
          (15,"The offer","reveal",[
              ("The knight takes on E6.",["moveAssessments/14"]),
              ("Black can take it right away.",["deepVerification/best/moves/0"])]),
          (16,"The queen moves first","critical",[
              ("Kasparov moves his queen to E7.",["moveAssessments/15"]),
              ("The capture will have to wait.",["moveAssessments/15","moveAssessments/17"])]),
          (0,"The immediate capture","variation",[
              ("Stockfish prefers taking right away.",["deepVerification/best","deepVerification/played"])]),
          (1,"The immediate capture","variation",[
              ("In that line, the pawn takes the knight.",["deepVerification/best/moves/0"])]),
          (16,"Back to the game","establishing",[
              ("Watch what White gets before the capture.",["moveAssessments/16","moveAssessments/17"])]),
          (17,"White uses the move","reveal",[
              ("Deep Blue uses that move to castle.",["moveAssessments/16"])]),
          (18,"Black takes the knight","reveal",[
              ("Now Black takes the knight.",["moveAssessments/17"])]),
          (19,"The bishop arrives","critical",[
              ("The bishop checks from G6.",["moveAssessments/18"])]),
          (20,"The king retreats","reveal",[
              ("Black’s king steps back to D8.",["moveAssessments/19"])]),
          (20,"Count the moves","final",[
              ("The question is when to take.",[]),
              ("What can your opponent do before you get to?",[])])
        ]
        openers={
            "pressure":("Keep your eye on Black’s king.",["positions/14"]),
            "tempo":("There are two ways this knight can come off.",["deepVerification/best","moveAssessments/17"]),
        }
        if treatment in openers:
            specs[0][3][0]=openers[treatment]
        scenes,claims=[],[]
        for index,(ply,title,preset,lines) in enumerate(specs):
            variation=index in (3,4)
            animated=index in (1,2,4,6,7,8,9)
            move=(deep["best"]["moves"][0] if variation else record["moveAssessments"][ply-1]["actual"]) if animated else None
            uci=move["uci"] if move else ""
            scene={"ply":ply,"title":title,"preset":preset,"transition":"glide" if animated else "cut",
                   "camera":{"focus":uci[2:4] or None,"zoom":1.10 if index in (1,2,8) else 1},
                   "phrases":[[text,.22,spoken(text)] for text,_ in lines]}
            if variation:
                scene["line"]="engine-choice"
            if animated:
                scene.update(anchor=0,highlights=[uci[:2],uci[2:4]],effect="check" if index==8 else "place")
            scenes.append(scene)
            for text,refs in lines:
                claims.append({"id":f"claim-{len(claims)+1}","text":text,"references":refs,
                               "category":"engine-hypothetical" if variation or any(x.startswith("deepVerification") for x in refs) else "game" if refs else "editorial",
                               "status":"verified" if refs else "editorial","limitations":["Finite-depth hypothetical line"] if variation else []})
    rates={}
    for scene in scenes:
        preset=scene["preset"]
        scene["lead"],scene["tail"],rate={
            "critical":(.32,.62,.91),"variation":(.15,.74,.95),"final":(.18,1.1,.94),
            "establishing":(.06,.38,1.01),
        }.get(preset,(.04,.28,1.07))
        for phrase in scene["phrases"]:
            rates[phrase[2]]=rate
    return scenes,claims,rates
