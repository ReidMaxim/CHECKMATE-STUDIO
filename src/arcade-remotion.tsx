import {AbsoluteFill,Audio,Composition,registerRoot,staticFile,useCurrentFrame} from 'remotion';
import '@fontsource/dm-sans/latin-700.css';
import cues from './arcade-cues.json';
import evidence from '../examples/analysis/legal-mate.json';
import './arcade.css';

const fps=30;
const seconds=26;
const cell=100;
const colors={cream:'#fff2ba',honey:'#f4bd57',violet:'#281a4b',purple:'#9a77e4',mint:'#8cf5cd',pink:'#ff659d'};
// Original 13-by-13 sprites, drawn for ARCADE//CHESS.
const art:Record<string,string[]>={
  p:['.....###.....','....#####....','....#####....','.....###.....','......#......','.....###.....','.....###.....','....#####....','....#####....','...#######...','..#########..','..#########..','.............'],
  r:['.##..###..##.','.##..###..##.','.###########.','..#########..','...#######...','....#####....','....#####....','....#####....','...#######...','...#######...','..#########..','..#########..','.............'],
  n:['....##.......','...#####.....','..########...','..#########..','.####.#####..','.##########..','..########...','....#####....','...######....','..#########..','..#########..','..#########..','.............'],
  b:['......#......','.....###.....','....#####....','...#####.#...','...####.##...','....#####....','.....###.....','.....###.....','....#####....','...#######...','..#########..','..#########..','.............'],
  q:['.#....#....#.','###..###..###','.##..###..##.','.###.###.###.','..#########..','...#######...','....#####....','....#####....','...#######...','...#######...','..#########..','..#########..','.............'],
  k:['......#......','.....###.....','......#......','..##..#..##..','.####.#.####.','.###########.','..#########..','...#######...','....#####....','...#######...','..#########..','..#########..','.............']
};
const coord=(square:string)=>['abcdefgh'.indexOf(square[0])*cell,(8-Number(square[1]))*cell];
function boardPieces(fen:string){
  return fen.split(' ')[0].split('/').flatMap((rank,y)=>{
    let x=0;
    return [...rank].flatMap(symbol=>{
      if(Number(symbol)){x+=Number(symbol);return [];}
      return [{symbol,x:x++*cell,y:y*cell}];
    });
  });
}
const reverseCues=[...cues].reverse();
const frames=(time:number)=>Math.round(time*fps);
const clamp=(value:number)=>Math.max(0,Math.min(1,value));

function Sprite({symbol,x,y,alpha}:{symbol:string;x:number;y:number;alpha:number}){
  const white=symbol===symbol.toUpperCase();
  const pixels=art[symbol.toLowerCase()].flatMap((row,j)=>[...row].flatMap((dot,i)=>dot==='.'?[]:[`M${i*5} ${j*5}h5v5h-5Z`])).join('');
  return <g transform={`translate(${Math.round(x)+17},${Math.round(y)+20})`} opacity={alpha}>
    <path d={pixels} transform="translate(4 6)" fill="#17102b"/>
    <path d={pixels} fill={white?colors.cream:colors.purple} stroke={white?'#6c4b45':'#301f5e'} strokeWidth="1"/>
  </g>;
}

function Arcade(){
  const frame=useCurrentFrame();
  const cue=reverseCues.find(item=>frames(item.time)<=frame) ?? cues[0];
  const move=evidence.moveAssessments[cue.ply-1]?.actual;
  const effect=cue.effect;
  const elapsed=frame-frames(cue.time);
  const hit=frames(cue.hit??0);
  const moveProgress=effect?clamp((elapsed-hit+12)/12):1;
  const landed=moveProgress===1;
  const ply=landed||!effect?cue.ply:cue.ply-1;
  const pos=evidence.positions[ply];
  const dest=effect&&move?coord(move.uci.slice(2,4)):null;
  const src=effect&&move?coord(move.uci.slice(0,2)):null;
  const mark=dest&&elapsed>=hit-12;
  const burst=elapsed-hit;
  const pieces=boardPieces(pos.fen);
  const moving=src&&!landed?pieces.find(piece=>piece.x===src[0]&&piece.y===src[1]):undefined;
  const settled=pieces.filter(piece=>piece!==moving);
  const whiteQueen=pieces.some(p=>p.symbol==='Q') && !(moving?.symbol==='Q');
  const mate=ply===13;
  const title=!landed && effect && effect!=='move' ? 'TACTIC IN PLAY' : cue.title;
  return <AbsoluteFill className="arcade">
    <div className="arcade-screen"/>
    <div className="arcade-wordmark">ARCADE<span>//</span>CHESS</div>
    <div className="arcade-title">{title}</div>
    <div className="arcade-hud">
      <div><span>WHITE</span><strong>{whiteQueen?'QUEEN ONLINE':'QUEEN DOWN'}</strong></div>
      <div><span>BLACK</span><strong>{mate?'CHECKMATED':move?.san.endsWith('+')&&landed?'IN CHECK':'KING ACTIVE'}</strong></div>
    </div>
    <div className="arcade-board">
      <svg viewBox="0 0 800 800" role="img" aria-label={pos.fen}>
        {Array.from({length:64},(_,i)=><rect key={i} x={i%8*cell} y={Math.floor(i/8)*cell} width={cell} height={cell}
          fill={(i+Math.floor(i/8))%2?'#514272':'#b2a0be'}/>)}
        {mark&&dest&&src&&<g stroke={effect==='capture'?colors.pink:colors.mint} strokeWidth="5" fill="none">
          <rect x={src[0]+4} y={src[1]+4} width="92" height="92" opacity=".52"/>
          <rect x={dest[0]+4} y={dest[1]+4} width="92" height="92"/>
        </g>}
        {settled.map(piece=><Sprite key={`${piece.x}:${piece.y}`} {...piece}
          alpha={moving&&dest&&piece.x===dest[0]&&piece.y===dest[1]?1-.7*moveProgress:1}/>)}
        {moving&&dest&&<Sprite symbol={moving.symbol} x={moving.x+(dest[0]-moving.x)*moveProgress}
          y={moving.y+(dest[1]-moving.y)*moveProgress-22*Math.sin(moveProgress*Math.PI)} alpha={1}/>}
        {dest&&effect!=='move'&&burst>=0&&burst<20&&Array.from({length:12},(_,i)=>{
          const angle=i*Math.PI/6;
          const distance=23+burst*3.7;
          return <rect key={i} x={Math.round(dest[0]+50+Math.cos(angle)*distance)} y={Math.round(dest[1]+50+Math.sin(angle)*distance)}
            width={i%2?8:12} height={i%2?8:12} fill={effect==='capture'?colors.pink:colors.mint} opacity={1-burst/20}/>;
        })}
      </svg>
    </div>
    <div className="arcade-move"><span>{lineLabel(ply)} · RECORDED LINE</span><strong>{evidence.moveAssessments[ply-1].actual.san}</strong></div>
    <div className="arcade-caption">{cue.caption}</div>
    <footer>LÉGAL MATE · PUBLISHED CONTINUATION</footer>
    <Audio src={staticFile('arcade-mix.wav')}/>
  </AbsoluteFill>;
}

function lineLabel(ply:number){
  const item=evidence.moveAssessments[ply-1];
  return `TURN ${item.moveNumber} · ${item.player.toUpperCase()}`;
}

registerRoot(()=> <Composition id="arcade-chess" component={Arcade} width={1080} height={1920} fps={fps} durationInFrames={fps*seconds}/>);
