import {useState} from 'react';

type Review = {
  provider:{mode:string; model:string|null};
  angle:string; selection:{id:string;reason:string};
  deepVerification:{disagreement:boolean;estimatedLoss:number;screeningLoss:number;settings:{limit:{depth:number}}};
  durationSeconds:number;
  claims:{id:string;text:string;category:string;references:string[]}[];
  scenes:{title:string;ply:number;frames:number;captions:{text:string}[]}[];
};
type Evidence = {game:{headers:{Event?:string}};storyCandidates:string[];criticalMoments:{id:string;move:string;summary:string}[]};
const reviews=Object.values(import.meta.glob<Review>('./storyteller-review.generated.json',{eager:true,import:'default'}));
const games=Object.entries(import.meta.glob<Evidence>('../examples/analysis/*.json',{eager:true,import:'default'}));
const workflow='https://github.com/ReidMaxim/CHECKMATE-STUDIO/actions/workflows/storyteller.yml';

export function StorytellerPanel({preview}:{preview:()=>void}){
  const [game,setGame]=useState(games[0]?.[0]);
  const [choice,setChoice]=useState('');
  const current=games.find(([path])=>path===game)?.[1];
  const review=game?.endsWith('/deep-blue.json') ? reviews[0] : undefined;
  const eligible=review && (!choice || review.selection.id===choice);
  return <section id="storyteller" className="analysis">
    <div className="heading"><h2>Storyteller</h2><p>Choose a candidate and inspect the evidence behind the documentary.</p></div>
    <div className="panel details">
      <label htmlFor="story-game">Analyzed game</label>
      <select id="story-game" value={game} onChange={e=>{setGame(e.target.value);setChoice('');}}>
        {games.map(([path,data])=><option key={path} value={path}>{data.game.headers.Event ?? path}</option>)}
      </select>
      <label htmlFor="story-candidate">Story candidate</label>
      <select id="story-candidate" value={choice} onChange={e=>setChoice(e.target.value)}>
        <option value="">Automatic · highest ranked</option>
        {current?.criticalMoments.filter(m=>current.storyCandidates.includes(m.id)).map(m=>
          <option key={m.id} value={m.id}>{m.move} · {m.id}</option>)}
      </select>
      {current?.criticalMoments.find(m=>m.id===(choice||current.storyCandidates[0]))?.summary}
      {eligible ? <>
        <h3>{review.angle}</h3>
        <p>{review.provider.mode==='offline-demonstration'?'Offline demonstration':review.provider.model} · {review.durationSeconds.toFixed(1)} seconds</p>
        <p>{review.selection.reason} · Stockfish depth {review.deepVerification.settings.limit.depth}</p>
        {review.deepVerification.disagreement && <p>Deeper verification reduced confidence in the screening estimate.</p>}
        <button onClick={preview}>Open documentary preview</button>
        <details><summary>Script and storyboard</summary><ol>{review.scenes.map((scene,index)=><li key={index}>
          <strong>{scene.title}</strong> · ply {scene.ply} · {(scene.frames/30).toFixed(1)} s
          <p>{scene.captions.map(cue=>cue.text).join(' ')}</p>
        </li>)}</ol></details>
        <details><summary>Claim evidence</summary><ul>{review.claims.map(claim=><li key={claim.id}>
          {claim.text}<br/><small>{claim.category} {claim.references.join(' · ')}</small>
        </li>)}</ul></details>
      </>:<p>A review draft for this selection is currently unavailable.</p>}
      <p><a href={workflow}>Storyteller renders ↗</a></p>
    </div>
  </section>;
}
