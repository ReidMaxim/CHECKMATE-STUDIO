import {boardPoint, type Project, type Snapshot} from './storyboard';

const glyph: Record<string,string> = {k:'♚',q:'♛',r:'♜',b:'♝',n:'♞'};
const squares = [...'87654321'].flatMap(rank => [...'abcdefgh'].map(file => file+rank));
const cell = 100;
type Props = {
  position: Snapshot; previous?: Snapshot; progress: number;
  orientation: Project['orientation']; theme: Project['theme'];
  highlights: string[]; arrows: [string,string][]; emphasis: number; animatedHighlights?: boolean;
};
export function Chessboard({position,previous,progress,orientation,theme,highlights,arrows,emphasis,animatedHighlights=false}:Props) {
  const moving = progress < 1 && previous && position.move;
  const palette = theme === 'forest' ? ['#b9b99a','#586955'] : ['#aeb8b9','#54646e'];
  const point = (square:string) => boardPoint(square,orientation).map(value => value*cell);
  const visible = moving ? previous : position;
  return <svg viewBox="0 0 800 800" aria-label={visible.fen} role="img" style={{display:'block',width:'100%'}}>
    <defs><marker id="tactical-tip" markerWidth="3" markerHeight="3" refX="2.5" refY="1.5" orient="auto">
      <path d="M0,0 L3,1.5 L0,3 Z" fill="#f9cf76"/>
    </marker></defs>
    {squares.map(square => {
      const [x,y] = point(square);
      const marked = highlights.includes(square);
      return <g key={square}>
        <rect x={x} y={y} width={cell} height={cell} fill={palette[(x/cell+y/cell)%2]}/>
        {marked && <rect x={x+3} y={y+3} width="94" height="94" fill="#edb956" fillOpacity={animatedHighlights ? .18+.12*emphasis : .25} stroke="#ffe1a0" strokeWidth="4"/>}
        {square === visible.check && <rect x={x+6} y={y+6} width="88" height="88" rx="12" fill="#a93426" fillOpacity=".75"/>}
        {y===700 && <text x={x+88} y={y+91} textAnchor="end" fill="#19261f" fontSize="15" fontWeight="800">{square[0]}</text>}
        {x===0 && <text x={x+8} y={y+18} fill="#19261f" fontSize="15" fontWeight="800">{square[1]}</text>}
      </g>;
    })}
    {Object.entries(visible.pieces).sort(([a],[b]) => Number(Boolean(moving && a===moving.source))-Number(Boolean(moving && b===moving.source))).map(([square,piece]) => {
      let [x,y] = point(square);
      const destination = moving && (moving.source===square ? moving.target : moving.rook?.[0]===square ? moving.rook[1] : null);
      if (destination) {
        const [tx,ty] = point(destination);
        x += (tx-x)*progress;
        y += (ty-y)*progress;
      }
      const light = piece === piece.toUpperCase();
      const fill = light ? '#fff0d6' : '#1c2521';
      const stroke = light ? '#272821' : '#c9c9ab';
      const opacity = moving && moving.capture===square ? 1-Math.max(0,(progress-.50)*2) : 1;
      if (piece.toLowerCase()==='p') return <path key={square} transform={`translate(${x},${y})`}
        d="M50 23a12 12 0 0 1 6 22c1 7 5 15 10 19h4v10H30V64h4c5-4 9-12 10-19a12 12 0 0 1 6-22Z"
        fill={fill} stroke={stroke} strokeWidth="2" opacity={opacity}/>;
      return <text key={square} x={x+50} y={y+77} textAnchor="middle" fontFamily="Noto Sans Symbols 2" fontSize="78"
        fill={fill} stroke={stroke} strokeWidth={light?2.1:1.15}
        paintOrder="stroke" opacity={opacity}>
        {glyph[piece.toLowerCase()]}
      </text>;
    })}
    {arrows.map(([from,to],index) => {
      const [x,y]=point(from).map(value=>value+50),[tx,ty]=point(to).map(value=>value+50);
      const length=Math.hypot(tx-x,ty-y);
      const stop=(1-29/length)*(.32+.68*emphasis);
      return <line key={index} x1={x} y1={y} x2={x+(tx-x)*stop} y2={y+(ty-y)*stop}
        stroke="#f9cf76" strokeWidth="9" strokeLinecap="round" markerEnd="url(#tactical-tip)" opacity={.88*emphasis}/>;
    })}
  </svg>;
}
