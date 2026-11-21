// Original pixel art on an integer coordinate grid. One SVG surface per scene.
const bodies:Record<string,string>={
  b:'M15 1h5v3h4v4h4v6h-3v5h-4v8h5v5h5v5H5v-5h5v-5h5v-8h-4v-5H8V8h4V4h3z',
  q:'M4 4h5v5h5V4h3V0h4v4h3v5h5V4h5v9h-3v7h-6v7h4v5h5v5H4v-5h5v-5h4v-7H7v-7H4z',
  n:'M12 2h6v4h5v4h6v5h4v6H21v-4h-5v5h6v5h6v5h5v5H3v-5h6v-5h2v-6H6V12h6z',
  k:'M15 0h6v5h6v5h-6v5h8v-5h5v10h-4v5h-6v5h5v3h5v4H4v-4h5v-3h5v-5H8v-5H4V10h5v5h6v-5H9V5h6z',
  p:'M14 5h9v4h4v10h-5v8h5v5h6v5H5v-5h6v-5h5v-8h-6V9h4z',
  r:'M4 4h6v6h5V4h6v6h5V4h6v13h-5v6h-5v6h6v4h5v4H3v-4h5v-4h6v-6H9v-6H4z',
};
const details:Record<string,string>={
 b:'M21 7h4v5h-4v4h-5v-4h5z M12 30h12v2H12z',
 q:'M10 12h17v3H10z M16 19h6v4h-6z M12 30h14v2H12z',
 n:'M23 12h4v4h-4z M10 14h4v7h-4z M12 29h14v2H12z',
 k:'M10 17h17v3H10z M15 24h9v3h-9z M11 32h16v2H11z',
 p:'M14 10h8v3h-8z M11 30h14v2H11z',
 r:'M8 13h20v3H8z M12 30h14v2H12z',
};

export function Fighter({piece,x,y,scale=1,face=1,alpha=1}:{piece:string;x:number;y:number;scale?:number;face?:number;alpha?:number}){
  const pale=piece===piece.toUpperCase(), form=piece.toLowerCase();
  return <g transform={`translate(${Math.round(x)} ${Math.round(y)}) scale(${scale*face} ${scale}) translate(-18 -37)`} opacity={alpha}>
    <path d={bodies[form]} fill="#110e20" transform="translate(2 2)"/>
    <path d={bodies[form]} fill={pale?'#f2b65e':'#647ac4'} stroke="#171225" strokeWidth="1.8"/>
    <path d={bodies[form]} fill="none" stroke={pale?'#ffdd89':'#a6b5fa'} strokeWidth=".7" transform="translate(-.4 -.45)"/>
    <path d={details[form]} fill={pale?'#803e64':'#201b46'}/>
    <path d="M7 34h24v2H7z" fill={pale?'#9c584c':'#46447e'}/>
  </g>;
}

export function Arena({mate=false}:{mate?:boolean}){
  return <g shapeRendering="crispEdges">
    <rect width="360" height="640" fill={mate?'#171d37':'#251a36'}/>
    {Array.from({length:17},(_,i)=><rect key={i} x="0" y={i*20+45} width="360" height="20"
      fill={mate?`rgb(${25+i},${31+i*2},${56+i*2})`:`rgb(${38+i*4},${25+i*2},${53+i*3})`}/>)}
    <path d="M126 280v-20h11v-13h14v-8h14v-6h31v6h14v8h14v13h11v45H126z" fill={mate?'#63c7bd':'#eb8e69'}/>
    {[271,280,290,302].map((y,i)=><rect key={y} x="124" y={y} width="113" height={2+i} fill={mate?'#2d4566':'#63405f'}/>)}
    <path d="M0 331h20v-11h16v-15h24v10h20v11h17v-8h23v13h24v-10h19v-6h18v-17h19v13h14v15h24v-10h18v-13h17v9h28v-12h29v14h30v70H0z" fill="#423557"/>
    <path d="M0 355h28v-13h19v-18h12v10h17v21h26v-12h22v9h30v-13h20v-15h13v13h18v11h34v-11h23v13h25v-19h20v-10h14v16h16v16h23v63H0z" fill="#2a2546"/>
    <path d="M0 381h360v259H0z" fill="#201b35"/>
    <path d="M0 381h360v5H0z M0 417h360v2H0z M0 459h360v3H0z M0 533h360v4H0z" fill="#4d3a59"/>
    {[-3,-2,-1,0,1,2,3].map(i=><path key={i} d={`M${180+i*30} 381L${180+i*105} 640`} stroke="#4d3a59" strokeWidth="2"/>)}
    <path d="M0 209h18v151h38v9H0zM360 209h-18v151h-38v9h56z" fill="#18152b"/>
    <path d="M0 210h32v6H0zM328 210h32v6h-32z" fill={mate?'#70d7bb':'#ecaa69'}/>
  </g>;
}
