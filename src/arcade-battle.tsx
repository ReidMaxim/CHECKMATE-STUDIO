import {AbsoluteFill,Audio,staticFile,useCurrentFrame} from 'remotion';
import evidence from '../examples/analysis/legal-mate.json';
import {Arena,Fighter} from './arcade-battle-art';
import './arcade-battle.css';

export const battleLength=435;
const between=(n:number,a:number,b:number)=>Math.min(1,Math.max(0,(n-a)/(b-a)));
const ease=(n:number)=>n*n*(3-2*n);
const square=(uci:string)=>['abcdefgh'.indexOf(uci[0]),8-Number(uci[1])];
const piecesAt=(ply:number)=>evidence.positions[ply].fen.split(' ')[0].split('/').flatMap((row,y)=>{
  let x=0;
  return [...row].flatMap(piece=>{if(Number(piece)){x+=Number(piece);return [];}return [{piece,x:x++,y}];});
});
const boards=Array.from({length:5},(_,i)=>piecesAt(i+9));

function Gameplay({frame}:{frame:number}){
  const ply=frame<42?9:frame<188?10:frame<224?11:frame<245?12:13;
  const next=frame>=173&&frame<188?11:frame>=209&&frame<224?12:0;
  const progress=next?ease(between(frame,next===11?173:209,next===11?188:224)):0;
  const move=evidence.moveAssessments[(next||ply)-1].actual;
  const [sx,sy]=square(move.uci.slice(0,2)),[dx,dy]=square(move.uci.slice(2,4));
  const pos=boards[ply-9];
  const focus=ply===9?[[6,4],[3,7]]:ply===12?[[2,5],[3,3]]:ply===13?[[3,3],[4,3],[4,1]]:ply===11?[[5,1],[4,0]]:[[dx,dy]];
  const side=evidence.positions[ply].fen.split(' ')[1]==='w'?'WHITE':'BLACK';
  const title=ply===13?'CHECKMATE':ply===11?'BLACK · ONE REPLY':`${side} TO MOVE`;
  const caption=ply===13?'Both knights close the net.':ply===9?'Bishop on g4. Queen on d1.':ply===10?'The bishop takes the queen.':ply===11?'Bxf7+ · The king must move.':'Ke7 · The knight is ready.';
  return <>
    <div className="battle-board-label"><span>{title}</span><strong>{ply<13&&'LAST · '}{evidence.moveAssessments[ply-1].actual.san}</strong></div>
    <svg viewBox="0 0 360 640" className="battle-stage" role="img" aria-label={evidence.positions[ply].fen}>
      <rect x="21" y="167" width="300" height="300" fill="#20192e" stroke="#bb8d79" strokeWidth="2"/>
      <g shapeRendering="crispEdges">
        {Array.from({length:64},(_,i)=>{
          const x=i%8,y=i>>3;
          return <rect key={i} x={23+x*37} y={169+y*37} width="37" height="37"
            fill={(x+y)%2?'#554264':'#a18a9b'}/>;
        })}
        {focus.map(([x,y])=><rect key={`${x}:${y}`} x={24+x*37} y={170+y*37} width="35" height="35" fill="none" stroke={ply===9?'#f8b369':'#8feece'} strokeWidth="2"/>)}
        {[...pos].sort((a,b)=>Number(a.x===sx&&a.y===sy)-Number(b.x===sx&&b.y===sy)).map(({piece,x,y})=>{
          const sliding=next&&x===sx&&y===sy;
          return <Fighter key={`${x}:${y}`} piece={piece} scale={.85}
            x={41+x*37+(sliding?(dx-sx)*37*progress:0)}
            y={202+y*37+(sliding?(dy-sy)*37*progress:0)}
            alpha={next&&x===dx&&y===dy?1-progress:1}/>;
        })}
      </g>
    </svg>
    <div className="battle-caption">{caption}</div>
  </>;
}

function Cinematic({frame,mate}:{frame:number;mate:boolean}){
  const age=frame-(mate?245:42);
  const hit=mate?66:47;
  const windup=ease(between(age,0,26));
  const leap=ease(between(age,mate?37:28,hit));
  const knock=ease(between(age,hit+7,hit+24));
  const aftermath=between(age,hit+13,hit+30);
  const x=86-16*windup+103*leap;
  const y=390-(mate?95:42)*Math.sin(Math.PI*leap);
  const marker=mate?'Nd5#':'Bxd1';
  const impact=age>=hit&&age<hit+15;
  return <>
    <svg viewBox="0 0 360 640" className="battle-stage" role="img" aria-label={`${marker} dramatization`}>
      <Arena mate={mate}/>
      <g shapeRendering="crispEdges">
        <ellipse cx={x} cy="391" rx="49" ry="8" fill="#141026" opacity=".65"/>
        <ellipse cx={264+29*knock} cy="391" rx="48" ry="8" fill="#141026" opacity={.65*(1-aftermath)}/>
        {leap>0&&leap<1&&<path d={`M${x-81} ${y-33}h55v6h-55z M${x-55} ${y-55}h38v4h-38z`}
          fill={mate?'#8df5cf':'#ef997d'} opacity=".65"/>}
        <Fighter piece={mate?'N':'b'} x={x} y={y} scale={3.4}/>
        <Fighter piece={mate?'k':'Q'} x={264+28*knock} y={390+18*knock} scale={3.5} face={-1} alpha={mate?1:1-aftermath}/>
        {impact&& <path d={mate?'M224 255h12l-22 56h42l-49 67h-15l25-55h-39z':'M273 245h12l-70 126h-17z'}
          fill={mate?'#aceccb':'#ffd29a'} opacity={1-(age-hit)/17}/>}
        {mate&&age>=hit&&<path d="M256 384h56v3h-56z" fill="#8df5cf"/>}
      </g>
    </svg>
    <div className="battle-cinematic-label"><span>{marker} · MOVE CINEMATIC</span>
      <strong>{age<hit?(mate?'KNIGHT FINISHER':'BISHOP VS. QUEEN'):(mate?'CHECKMATE':'QUEEN DOWN')}</strong></div>
    <div className="battle-caption">{age<hit?(mate?'White knight vs. Black king':'Black bishop vs. White queen'):(mate?'White wins the match.':'The queen falls.')}</div>
  </>;
}

export function ArcadeBattle(){
  const frame=useCurrentFrame();
  const cinematic=frame>=42&&frame<135||frame>=245&&frame<354;
  return <AbsoluteFill className={`battle ${cinematic?'battle-cinematic':'battle-gameplay'}`}>
    {cinematic?<Cinematic frame={frame} mate={frame>=245}/>:<Gameplay frame={frame}/>}
    <header className="battle-brand">ARCADE<span>//</span>CHESS</header>
    <footer className="battle-credit">LÉGAL MATE · RECORDED LINE</footer>
    <Audio src={staticFile('arcade-battle.mp3')}/>
  </AbsoluteFill>;
}
