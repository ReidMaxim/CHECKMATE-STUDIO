import {mkdir, readFile, writeFile} from 'node:fs/promises';
import {join} from 'node:path';

const out = process.argv[2] ?? 'out/stockfool/brand';
await mkdir(out, {recursive:true});
const identity = JSON.parse(await readFile('brand/stockfool/identity.json', 'utf8'));
const {main, accent, dark, light, warning} = identity.colors;
const svg = (w,h,body) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${body}</svg>\n`;
const group = (transform,body) => `<g transform="${transform}">${body}</g>`;
const rect = (w,h,fill,x=0,y=0,rx=0) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}"/>`;
const label = (str,x,y,size,color=light,serif=false) => `<text x="${x}" y="${y}" fill="${color}" font-family="${serif ? 'Liberation Serif' : 'Liberation Sans'}" font-size="${size}" font-weight="700">${str}</text>`;

const glyphs = {
  S:'M25 3H8L3 8V17L8 21H20L25 26V34L20 39H3',
  T:'M2 3H27M15 3V39', O:'M8 3H21L26 8V34L21 39H8L3 34V8Z',
  C:'M25 3H9L3 9V33L9 39H25', K:'M4 3V39M25 3L8 22L26 39',
  F:'M4 39V3H26M4 20H22', L:'M4 3V39H26'
};
function wordmark(ink=light, end=accent, name=identity.name) {
  return `<g fill="none" stroke-width="5" stroke-linejoin="bevel" stroke-linecap="square">`
    + [...name].map((letter,i)=>`<path transform="translate(${i*36+3} 4)" stroke="${i<5?ink:end}" d="${glyphs[letter]}"/>`).join('')+'</g>';
}
function fish(simple=false) {
  return `<g stroke="${dark}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round">
    <path d="M62 82 14 54l9 35-9 34 48-25" fill="${main}"/>
    <path d="M76 65q6-30 32-43l12 28M79 109l10 29 27-23" fill="${main}"/>
    <path d="M48 87Q91 36 150 50q36 8 48 32-5 31-52 40Q90 131 48 87Z" fill="${main}"/>
    <path d="M62 101q55 25 112-5-18 22-43 23-38 4-69-18Z" fill="#548775" stroke="none"/>
    <path d="M124 46l-6-21 15 5 9-19 9 18 16-6-5 22Z" fill="${accent}"/>
    <path d="M142 10V3m-5 4h10" fill="none" stroke="${accent}" stroke-width="4"/>
    ${simple?'':`<path d="M95 83q-18-5-25 5 12 12 28 9" fill="#548775" stroke-width="5"/>`}
    <path d="M153 74q13-5 23 0" fill="none" stroke-width="5"/>
    <circle cx="165" cy="82" r="4.5" fill="${dark}" stroke="none"/>
    <path d="M156 99q12 4 23-4" fill="none" stroke-width="4"/>
  </g>`;
}

const lockup = (ink=light, tagline=accent) => wordmark(ink,tagline)+label(identity.tagline,3,79,21,ink);
const checker = (color,size=80) => `<defs><pattern id="check" width="${size*2}" height="${size*2}" patternUnits="userSpaceOnUse"><rect width="${size}" height="${size}" fill="${color}"/><rect x="${size}" y="${size}" width="${size}" height="${size}" fill="${color}"/></pattern></defs>`;
const files = {
  'wordmark-horizontal':svg(328,49,wordmark()),
  'wordmark-dark':svg(360,82,rect(360,82,dark,0,0,12)+group('translate(16 16)',wordmark())),
  'wordmark-light':svg(360,82,rect(360,82,light,0,0,12)+group('translate(16 16)',wordmark(dark,'#305D49'))),
  'wordmark-mono':svg(328,49,wordmark(dark,dark)),
  'wordmark-compact':svg(184,108,wordmark(light,light,'STOCK')+group('translate(0 56)',wordmark(accent,accent,'FOOL'))),
  'tagline-lockup':svg(328,91,lockup()),
  'mascot-full':svg(224,154,group('translate(5 4)',fish())),
  'mascot-icon':svg(224,154,group('translate(5 4)',fish(true))),
  'mascot-sticker':svg(256,256,`<circle cx="128" cy="128" r="122" fill="${dark}" stroke="${accent}" stroke-width="8"/>`+group('translate(20 48)',fish())),
  'profile-avatar':svg(800,800,rect(800,800,dark)+`<circle cx="400" cy="400" r="281" fill="#253C30" stroke="${accent}" stroke-width="6"/>`+group('translate(142 219) scale(2.45)',fish(true))),
  'channel-banner':svg(2560,1440,checker('#1A2B23',120)+rect(2560,1440,dark)+rect(2560,1440,'url(#check)')+
    rect(1472,348,dark,544,546,32)+rect(6,232,accent,631,604,3)+group('translate(690 641) scale(2)',lockup())+
    group('translate(1450 554) scale(2.35)',fish())),
  'opening-minimal':svg(205,42,group('translate(1 9) scale(.53)',wordmark())),
  'opening-mascot':svg(205,42,group('translate(0 0) scale(.27)',fish(true))+group('translate(65 11) scale(.42)',wordmark())),
  'closing-lockup':svg(464,133,rect(52,3,accent,0,7,1)+group('translate(0 31) scale(.7)',lockup()))
};

const cover = (name, lines, useFish, sub, motif) => svg(1080,1920,
  checker('#1A2B23',135)+rect(1080,1920,dark)+rect(1080,1920,'url(#check)')+
  rect(904,1420,'#14221B',88,245,22)+rect(6,118,accent,124,331,2)+
  group('translate(155 340) scale(1.6)',wordmark())+
  label(sub,126,566,34,accent)+
  lines.map((line,i)=>label(line,119,737+i*126,112,light,true)).join('')+
  (useFish?group('translate(525 1048) scale(2)',fish()):'')+motif+
  label('LASKER  /  BAUER',126,1584,37,accent)+label(name,126,1630,29,main));
const bishop = `<path d="M100 296h224l14 23H87zM116 274q81-40 79-98l-27-28 40-66 43 66-25 28q-4 58 78 98z" fill="${light}"/><path d="m196 137 38-35" stroke="${dark}" stroke-width="11"/><circle cx="208" cy="70" r="13" fill="${accent}"/>`;
files['cover-documentary']=cover('AMSTERDAM 1889',['Why give up','both bishops?'],false,'THE DOUBLE BISHOP SACRIFICE',
  group('translate(195 962) scale(1.5)',bishop)+group('translate(550 1012) scale(1.1)',bishop));
files['cover-humor']=cover(identity.tagline,['Both bishops?','Bold choice.'],true,'A VERY QUESTIONABLE MOVE',
  group('translate(32 1020) scale(1.18)',bishop));
files['cover-hybrid']=cover('THE DOUBLE BISHOP SACRIFICE',['Two pawns.','Two bishops.'],true,'WHY GIVE UP BOTH?',
  group('translate(75 1010) scale(1.15)',bishop));
files['palette']=svg(1000,490,rect(1000,490,dark)+group('translate(50 46) scale(1.2)',wordmark())+
  Object.entries({main,accent,dark,light,warning}).map(([key,v],i)=>{
    const x=50+i*183;return rect(165,177,v,x,151,10)+label(key.toUpperCase(),x,380,23)+label(v,x,419,22,accent);
  }).join(''));
await Promise.all(Object.entries(files).map(([name,source])=>writeFile(join(out,`${name}.svg`),source)));
