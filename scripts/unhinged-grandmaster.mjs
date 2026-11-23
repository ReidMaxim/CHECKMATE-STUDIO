import {mkdir, writeFile} from 'node:fs/promises';
import {join} from 'node:path';

const output = process.argv[2] ?? 'out/unhinged-grandmaster/brand';
await mkdir(output, {recursive:true});
const ivory='#F6F1E3', antique='#D6B26A', jade='#86A699', dark='#0B120F';
const warm='#BEAE8C', glint='#FFEDBD', bronze='#826138', forest='#1B332A';
const path=(d,fill,stroke='none',sw=0)=>`<path d="${d}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/>`;
const group=(transform,art)=>`<g transform="${transform}">${art}</g>`;
const label=(x,y,size,text,fill=ivory)=>`<text x="${x}" y="${y}" fill="${fill}" font-family="Liberation Serif, Georgia, serif" font-style="italic" font-size="${size}" letter-spacing="2.7">${text}</text>`;
const svg=(w,h,body)=>`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${body}</svg>\n`;
const outline='M234 66 279 89 321 85 354 114 402 132 447 141 435 261 417 330 368 386 235 460 103 386 52 331 33 262 20 141 73 130 119 111 154 84 194 89Z';
const body='M229 236C253 260 280 277 316 285 354 293 375 314 377 337L344 387 353 416C303 449 196 453 123 418l9-38 33-30 41-57Z';
const head='M171 154 224 118 293 129 323 154 320 202 302 250 297 278 245 284 188 266 182 226 164 203 169 185 159 174Z';
const crown='M159 150 132 78 171 104 163 57 199 91 238 15 274 88 313 36 296 122 310 148C266 118 200 122 159 150Z';
const gem='M239 52 259 79 241 108 220 81Z';
const question='M0 15C0 5 9 0 21 0 34 0 43 7 43 18 43 27 38 32 30 37c-5 4-7 7-7 12H11c0-10 4-15 11-20 6-4 9-7 9-12 0-5-4-8-10-8-6 0-10 3-10 8Z M12 57a7 7 0 1 1 14 0 7 7 0 0 1-14 0Z';
const collar='M139 257C158 232 232 226 292 235 328 240 346 252 326 269 298 292 215 316 150 342 109 357 93 376 128 397 75 383 85 357 138 333 202 304 278 279 309 261 332 246 276 242 235 244 195 244 147 254 148 267 149 277 168 282 183 286 153 283 125 275 139 257Z';
const glimmer='M0-23 7-7 23 0 7 7 0 23-7 7-23 0-7-7Z';

function knight(){
  return path('M4 111q20-7 26-34L20 84 9 72l4-19 18-17 9-20 10 10 11-12 4 14q29 5 43 31l-12-5 11 18-13-6 6 23-11-8q3 18 15 29Z','#557A68',dark,5)+
    path('M18 64l15-22 11-6 9-1 4 7-14 6-8 11-12 2-6 10Z',ivory)+
    path('M57 32q36 16 38 62l-16-7-10-28-16-15Z',jade)+path('M34 53l9-6 6 1-11 6Z M18 68l5-2-4 7Z',dark)+path('M64 36l16 11 8 13-11-8 13 29-10-8-10-22Z','#C2D6C6')+
    path('M20 111q38-17 75-3l13 16H3Z','#365748',dark,4)+path('M15 113q40-8 76-1l6 4H11Z',jade);
}

function emblem(level='full',mono=null){
  const full=level==='full', micro=level==='micro';
  const ink=mono??ivory, gold=mono??antique, edge=mono??jade;
  const shade=mono?'none':warm, deep=dark;
  const symbols=full?group('translate(64 193) scale(.83)',knight())+group('translate(404 193) scale(-.83 .83)',knight()):'';
  const checker=full?`<defs><clipPath id="shield"><path d="${outline}"/></clipPath><pattern id="tiles" width="60" height="60" patternUnits="userSpaceOnUse"><rect width="30" height="30" fill="#315447"/><rect x="30" y="30" width="30" height="30" fill="#315447"/></pattern></defs><rect x="28" y="108" width="412" height="255" fill="url(#tiles)" clip-path="url(#shield)" opacity=".7"/>`:'';
  let art = micro ? '' : path(outline,forest,gold,10)+checker+
    path('M26 148 40 255 60 323 112 383 235 451 108 397 51 335 29 263 19 143Z',full?bronze:gold)+
    (full?path('M23 143 73 131 119 112 154 85 176 92 124 120 77 141 31 151Z',glint)+
      path('M439 145 420 255 403 321 358 375 235 443 368 386 417 330 435 261 447 141Z',bronze)+
      path('M27 307 76 333 127 395 87 367Z M443 307 394 333 343 395 385 367Z',gold)+symbols:'');
  if(!micro){
    art+=path(body,ink,dark,7)+path('M246 262 281 277 311 285 299 306 276 334 214 358 146 376 206 330Z',shade)+
      path('M128 385C187 361 278 360 348 390l5 25c-76-21-154-18-230 3Z',deep)+
      path('M138 391c62-23 131-20 198 1l13 11c-73-20-143-20-215 3Z',gold)+
      path('M319 287 342 294 327 310 304 303Z M283 325 304 303 327 310 310 332Z M327 310 350 318 333 340 310 332Z M267 349 283 325 310 332 292 356Z M310 332 333 340 316 363 292 356Z',deep)+
      path('M353 299 372 320 371 342 348 373 359 340 340 330Z',edge)+
      (full?path('M343 294 361 303 350 318 327 310Z M333 340 354 347 339 371 316 363Z',shade)+
        path('M146 414c35-10 73-13 101-10l-13 9c-32 0-63 4-96 10Z',shade):'');
  }
  art+=path(head,ink,dark,micro?10:7)+
    path('M231 130 294 129 323 154 320 202 302 250 297 278 237 279 232 245 241 229 232 211 235 188 226 173Z',deep)+
    path('M173 191 185 215 184 239 194 259 182 250 179 225 164 204Z',shade)+
    path('M226 219 232 225 230 232 221 226 213 225Z',shade)+
    path('M163 174Q184 169 225 155l-5 11Q195 191 173 184Z',deep)+
    path('M173 178q22-2 41-11-13 19-32 17Z',ink)+path('M188 175l9-3-1 8-6 1Z',deep)+
    (full?path('M166 188q15 7 31 0l9-6q-9 15-29 13Z',warm):'')+
    group('translate(257 155) scale(1.11 1.22)',path(question,ink))+
    path(crown,gold,dark,7)+
    path('M141 89 171 104 160 70 199 91 238 15 229 75 201 113 166 136Z',mono?'none':glint)+
    path('M239 23 274 88 310 44 294 116 276 104 265 93 249 108 235 91Z',mono?'none':bronze)+
    path('M158 145C189 113 268 105 297 128l13 20c-44-28-107-20-151 15Z',deep)+
    path('M160 143c35-26 102-37 137-8l6 9c-40-26-104-14-145 10Z',ink)+
    path(gem,mono?dark:edge,dark,5)+
    path('M239 57 239 81 223 81Z',mono?gold:'#C2E0CE')+
    path('M239 81 256 79 241 104Z',mono?gold:'#316254');
  if(micro){
    return group('translate(-81 4) scale(1.32)',art+
      path('M181 254Q238 227 300 247l6 16q-70-16-123 9Z',gold,dark,6));
  }
  return art+path(collar,ink,dark,5)+
    (full?path('M141 339c50-24 119-49 165-73-36 27-100 48-160 77-27 13-43 23-43 31-4-8 11-22 38-35Z',warm)+
      group('translate(235 434)',path(glimmer,gold,dark,2))+path('M219 434h16v-16l5 15 12 1-15 5-2 14-3-14Z',glint):'');
}

const letters={
  S:'M4 8 14 0h34l-4 17-9-7H19l-3 9 26 16-7 22-12 8H0l5-20 8 9h12l4-11L3 26Z',
  T:'M1 0h48l-3 20-8-9H31L23 53l6 12H4l7-12 9-42h-8L1 19Z',
  O:'M8 9 19 0h22l9 10-8 45-10 10H10L0 55Zm13 3-8 40h17l7-40Z',
  C:'M9 8 20 0h30l-4 20-10-9H23L15 53h14l12-11-4 23H10L0 54Z',
  K:'M4 0h25l-8 10-3 16L38 6l-3-6h23L33 27l16 29 11 9H31l-9-22-8 9-1 5 6 8H-4l7-9 9-46Z',
  F:'M5 0h47l-4 20-9-9H26l-3 14h11l8-6-5 23-6-6H21l-4 20 7 9H-3l7-10 10-44Z',
  L:'M6 0h27l-9 11-8 43h15l12-14-4 25H-4l8-11 9-43Z'
};
const word=(color=ivory)=>'<g fill-rule="evenodd">'+[...'STOCKFOOL'].map((l,i)=>
  group(`translate(${12+i*58} ${i===0||i===8?0:5}) scale(1 ${i===0||i===8?1.15:1})`,path(letters[l],color))).join('')+'</g>';
const tagline='Powered by Questionable Moves.';
const assets={
  'full-emblem':svg(468,468,emblem()),
  'standard-emblem':svg(468,468,emblem('standard')),
  'micro-icon':svg(468,468,emblem('micro')),
  'wordmark':svg(540,78,word()),
  'watermark':svg(468,468,`<g opacity=".65">${emblem('micro')}</g>`),
  'horizontal-lockup':svg(860,225,group('translate(7 4) scale(.462)',emblem('standard'))+
    group('translate(235 53) scale(1.13)',word())+label(250,171,32,tagline,antique)),
  'stacked-lockup':svg(620,685,group('translate(76 2)',emblem())+group('translate(39 490)',word())+label(62,620,32,tagline,antique)),
  'avatar':svg(800,800,`<rect width="800" height="800" rx="120" fill="${dark}"/>`+
    group('translate(69 42) scale(1.42)',emblem('standard'))),
  'palette':svg(1000,370,`<rect width="1000" height="370" fill="${dark}"/>`+
    group('translate(35 30) scale(.62)',word())+Object.entries({Ivory:ivory,'Antique Gold':antique,'Sage / Jade':jade,Charcoal:dark}).map(([labelText,color],i)=>{
      const x=35+241*i;
      return path(`M${x} 120h204v109h-204Z`,color,jade,1)+label(x,266,25,labelText)+label(x,302,23,color,antique);
    }).join(''))
};
// Knock out the paper-colored areas so the one-ink assets remain transparent.
for(const [name,ink] of [['single-color-light',ivory],['single-color-dark',dark]]){
  const black=emblem('standard','#FFFFFF').replaceAll(forest,'#000000').replaceAll(dark,'#000000');
  assets[name]=svg(468,468,`<defs><mask id="ink" maskUnits="userSpaceOnUse" x="0" y="0" width="468" height="468">${black}</mask></defs><rect width="468" height="468" fill="${ink}" mask="url(#ink)"/>`);
}
await Promise.all(Object.entries(assets).map(([name,data])=>writeFile(join(output,name+'.svg'),data)));
