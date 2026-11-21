import {useState} from 'react';
import {Chessboard} from './Chessboard';
import type {Snapshot} from './storyboard';
import './analysis.css';

type Score = {cp:number|null; mate:number|null; expectedWhite:number};
type Move = {san:string; uci:string; fen:string};
type Line = {fen:string; moves:Move[]; evaluation:Score; depth:number; rank:number};
type Moment = {id:string; ply:number; category:string; score:number; summary:string; move:string;
  before:Score; after:Score; recommended:Line; dimensions:Record<string,number>};
type Evidence = {game:{headers:Record<string,string>; pgn:string}; source:string|null; engine:{name:string};
  positions:{fen:string; evaluation:Score; lines:Line[]}[];
  moveAssessments:{actual:Move; bestMove:Move; quality:string; playedLine:Line}[];
  criticalMoments:Moment[]; storyCandidates:string[]; warnings:string[]};

const files = import.meta.glob<Evidence>('../examples/analysis/*.json',{eager:true,import:'default'});
const examples = Object.entries(files).map(([path,data])=>[path.split('/').at(-1)!,data] as const);
const categories:Record<string,string> = {'allows-mate':'Allows mate','endgame-turn':'Endgame turning point',
  'major-blunder':'Major blunder candidate','missed-opportunity':'Missed opportunity','mating-sequence':'Mating sequence',
  'sacrifice-candidate':'Sacrifice candidate','evaluation-reversal':'Evaluation reversal','tactical-combination':'Tactical combination'};
const dimensions:Record<string,string> = {impact:'Evaluation impact',tactics:'Tactics',clarity:'Visual clarity',
  surprise:'Surprise',education:'Teaching value',shortLine:'Short variation',hook:'Story hook',confidence:'Search depth'};

function label(value:Score) {
  if (value.mate===0) return value.expectedWhite===1 ? 'White checkmates' : 'Black checkmates';
  if (value.mate!==null) return `${value.mate>0?'White':'Black'} mate in ${Math.abs(value.mate)}`;
  const pawns=(value.cp ?? 0)/100;
  return `${pawns>0?'+':''}${pawns.toFixed(2)} for White`;
}

function snapshot(fen:string,san:string):Snapshot {
  const [placement,turn] = fen.split(' ');
  const pieces:Snapshot['pieces'] = {};
  placement.split('/').forEach((rank,y)=>{
    let x=0;
    for(const symbol of rank){
      const spaces=Number(symbol);
      if(spaces) x+=spaces;
      else pieces[`${'abcdefgh'[x++]}${8-y}`]=symbol as Snapshot['pieces'][string];
    }
  });
  const check=/[+#]$/.test(san)?Object.keys(pieces).find(square=>pieces[square]===(turn==='w'?'K':'k'))??null:null;
  return {fen,pieces,check,mate:san.endsWith('#'),legal:0};
}

function download(name:string,data:Evidence) {
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
  const link=document.createElement('a');
  link.href=url;
  link.download=name;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),30000);
}

function GameAnalysis({file,data}:{file:string;data:Evidence}) {
  const [ply,setPly]=useState(0);
  const [active,setActive]=useState<Moment>();
  const [line,setLine]=useState<Line>();
  const [linePly,setLinePly]=useState(0);
  const assessment=data.moveAssessments[ply-1];
  const position=data.positions[ply];
  const compare=active?data.moveAssessments[active.ply-1]:assessment;
  const recommended=active?.recommended ?? data.positions[Math.max(0,ply-1)].lines[0];
  const last=line?line.moves[linePly-1]:assessment?.actual;
  const fen=line?last?.fen??line.fen:position.fen;
  const end=data.positions.length-1;
  const index=line?linePly:ply;
  const max=line?line.moves.length:end;
  function seek(next:number){if(line){setLinePly(next);}else{setPly(next);setActive(undefined);}}
  function alternate(next:Line){setLine(next);setLinePly(0);}
  function select(moment:Moment){
    setLine(undefined);
    setPly(moment.ply-1);
    setActive(moment);
    document.getElementById('analysis-board')?.scrollIntoView({block:'nearest'});
  }
  return <div className="analysis-grid">
    <section id="analysis-board" className="panel details">
      <h3>{line?'Engine variation':active&&ply===active.ply-1?'Position before the critical move':'Recorded game'}</h3>
      <p className="muted">{line?'Hypothetical continuation':`Position ${ply} of ${end}`} · {last?.san ?? 'Starting position'}</p>
      <div className="analysis-board"><Chessboard position={snapshot(fen,last?.san??'')} progress={1} orientation="white"
        theme="forest" highlights={last?[last.uci.slice(0,2),last.uci.slice(2,4)]:[]} arrows={[]} emphasis={1}/></div>
      <div className="analysis-controls">
        <button disabled={!index} onClick={()=>seek(index-1)}>Previous</button>
        <button disabled={index===max} onClick={()=>seek(index+1)}>Next</button>
        {line && <button onClick={()=>setLine(undefined)}>Back to game</button>}
      </div>
      <label htmlFor="analysis-ply">{line?'Variation moves':'Game positions'}</label>
      <input id="analysis-ply" type="range" min={0} max={max} value={index} onChange={e=>seek(Number(e.target.value))}/>
      <p>{line?`Root evaluation: ${label(line.evaluation)} · depth ${line.depth}`:label(position.evaluation)}</p>
      {line && <p className="muted">{line.moves.map(move=>move.san).join(' · ')}</p>}
      <svg viewBox="0 0 300 75" role="img" aria-label="White expected score by ply, with even marked across the middle">
        <path d="M0 37.5H300" stroke="#64766a" strokeDasharray="3 4"/>
        <polyline points={data.positions.map((p,i)=>`${5+290*i/Math.max(1,end)},${70-65*p.evaluation.expectedWhite}`).join(' ')}
          fill="none" stroke="#e9c484" strokeWidth="2"/>
        <circle cx={5+290*ply/Math.max(1,end)} cy={70-65*position.evaluation.expectedWhite} r="4" fill="#fff0d6"/>
      </svg>
      <p className="muted">Stockfish expected score · White at the top</p>
      {compare && <div className="analysis-compare">
        <p><strong>Played</strong> {compare.actual.san} · {compare.quality}
          {active && <> <button onClick={()=>{setPly(active.ply);setLine(undefined);}}>Show played move</button></>}</p>
        {recommended && <p><strong>Engine preference</strong> {compare.bestMove.san} <button onClick={()=>alternate(recommended)}>Replay</button></p>}
        <p><button onClick={()=>alternate(compare.playedLine)}>Replay engine line for played move</button></p>
        {active && <p className="muted">Before {label(active.before)} → After {label(active.after)}</p>}
      </div>}
    </section>
    <div className="sidebar">
      <section className="panel details">
        <h3>{data.game.headers.Event ?? 'PGN example'}</h3>
        <p>{[data.game.headers.White,data.game.headers.Black].filter(Boolean).join(' vs. ')}</p>
        <p className="muted">{[data.game.headers.Date,data.game.headers.Site,data.game.headers.Result,data.engine.name].filter(Boolean).join(' · ')}</p>
        {data.source && (/^https?:\/\//.test(data.source)?<p><a href={data.source}>PGN source ↗</a></p>:<p>{data.source}</p>)}
        <button onClick={()=>download(file,data)}>Download evidence JSON</button>
        <details><summary>View PGN</summary><pre>{data.game.pgn}</pre></details>
      </section>
      <section className="panel details">
        <h3>Ranked story candidates</h3>
        {!data.storyCandidates.length && <p>No moment cleared the ranking threshold.</p>}
        {data.storyCandidates.map(id=>data.criticalMoments.find(m=>m.id===id)).map(moment=>moment &&
          <article key={moment.id} className="analysis-moment">
            <button onClick={()=>select(moment)} aria-pressed={active?.id===moment.id}>
              <strong>{moment.move} · {categories[moment.category]}</strong><span>{moment.score.toFixed(1)} / 100</span>
            </button>
            <p>{moment.summary}</p><p className="muted">Before {label(moment.before)} → After {label(moment.after)}</p>
            <details><summary>Why it ranked here</summary><dl>{Object.entries(moment.dimensions).map(([key,value])=>
              <div key={key}><dt>{dimensions[key]}</dt><dd>{Math.round(value*100)}%</dd></div>)}</dl></details>
          </article>)}
        {data.criticalMoments.some(moment=>!data.storyCandidates.includes(moment.id)) &&
          <details><summary>Other detected moments</summary>
            {data.criticalMoments.filter(moment=>!data.storyCandidates.includes(moment.id)).map(moment=>
              <p key={moment.id}><button onClick={()=>select(moment)}>{moment.move} · {categories[moment.category]}</button></p>)}
          </details>}
        <details><summary>Analysis limitations</summary><ul>{data.warnings.map(warning=><li key={warning}>{warning}</li>)}</ul></details>
      </section>
    </div>
  </div>;
}

export function AnalysisPanel() {
  const [file,setFile]=useState(examples[0]?.[0]);
  const match=examples.find(([name])=>name===file);
  return <section className="analysis" id="analysis">
    <div className="heading"><h2>Chess intelligence</h2><p>Replay the game and compare the actual move with Stockfish’s line.</p></div>
    <label htmlFor="analysis-game">Example PGN</label>
    <select id="analysis-game" value={file} onChange={e=>setFile(e.target.value)}>
      {examples.map(([name,data])=><option value={name} key={name}>{data.game.headers.Event ?? name}</option>)}
    </select>
    {match ? <GameAnalysis key={match[0]} file={match[0]} data={match[1]}/> : <p>No precomputed analysis is available.</p>}
  </section>;
}
