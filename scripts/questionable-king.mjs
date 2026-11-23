import {mkdir, readFile, writeFile} from 'node:fs/promises';
import {join} from 'node:path';

const folder = process.argv[2] ?? 'out/questionable-king';
const {name, tagline, colors} = JSON.parse(await readFile('brand/stockfool/identity.json','utf8'));
const {main, accent, dark, light} = colors;
const path = (d,fill=light) => `<path d="${d}" fill="${fill}"/>`;
const rect = (x,y,w,h,fill,rx=0) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}"/>`;
const circle = (x,y,r,fill) => `<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}"/>`;
const group = (transform,body) => `<g transform="${transform}">${body}</g>`;
const label = (x,y,size,value,fill=light,weight=700,spacing=0) =>
  `<text x="${x}" y="${y}" fill="${fill}" font-family="Liberation Sans, sans-serif" font-weight="${weight}" font-size="${size}" letter-spacing="${spacing}">${value}</text>`;
const svg = (w,h,body) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${body}</svg>\n`;

const question = 'M0 13C0 5 6 0 15 0c9 0 15 5 15 13 0 6-3 9-8 13l-3 3v4H9v-6c0-4 3-7 7-10 2-2 4-3 4-5 0-2-2-4-5-4s-5 2-5 5Z M9 39h10v10H9Z';
const cross = 'M59 8h10v11h13v10H69v13H59V29H46V19h13Z';
const king = 'M45 42h38l12 14-13 17 7 19H39l7-19-13-17Z M35 97h58l8 13H27Z M26 116h76v6H26Z';

const marks = [
  {
    id:'confused-king', title:'Confused King', note:'The classic king, flanked by two questions.',
    art: () => path(cross,accent)+path(king)+
      group('translate(9 20) rotate(-13) scale(.69)',path(question,main))+
      group('translate(102 14) rotate(13) scale(.67)',path(question,accent))
  },
  {
    id:'king-of-questions', title:'King of Questions', note:'The question mark takes the crown.',
    art: () => path('M34 17l17 8L64 8l13 17 17-8-7 27H41Z',accent)+
      path('M42 48h44l-3 7H45Z',main)+group('translate(43 61) scale(1.41 1.13)',path(question))
  },
  {
    id:'questionable-king', title:'Questionable King', note:'A question cut from the body of the piece.',
    art: () => path(cross,accent)+
      '<defs><mask id="king-question" maskUnits="userSpaceOnUse" x="0" y="0" width="128" height="128">'+
      rect(0,0,128,128,'white')+group('translate(50 48) scale(.93 .91)',path(question,'black'))+'</mask></defs>'+
      '<g mask="url(#king-question)">'+path('M40 36h48l15 17-14 22 7 22H32l7-22-14-22Z')+'</g>'+
      path('M29 103h70l10 16H19Z',main)
  }
];

await mkdir(folder,{recursive:true});
const save = (file,content) => writeFile(join(folder,file+'.svg'),content);
for (const mark of marks) {
  const {id,art} = mark;
  const lock = (x,y,scale=1) => group(`translate(${x} ${y}) scale(${scale})`,
    art()+rect(158,16,2,99,main)+label(196,64,64,name,light,700,3)+label(200,107,29,tagline,accent,400));
  await Promise.all([
    save(id,svg(128,128,art())),
    save(id+'-avatar',svg(800,800,rect(0,0,800,800,dark)+circle(400,400,301,'#1B3026')+
      `<circle cx="400" cy="400" r="301" fill="none" stroke="${main}" stroke-opacity=".48" stroke-width="3"/>`+
      group('translate(176 172) scale(3.5)',art()))),
    save(id+'-lockup',svg(685,150,lock(10,10))),
    save(id+'-banner',svg(2560,1440,
      '<defs><pattern id="check" width="240" height="240" patternUnits="userSpaceOnUse">'+
      rect(0,0,120,120,'#172820')+rect(120,120,120,120,'#172820')+'</pattern></defs>'+
      rect(0,0,2560,1440,dark)+rect(0,0,2560,1440,'url(#check)')+
      rect(549,563,1462,314,'#192C23',20)+rect(549,563,1462,3,main)+lock(745,615,1.66)))
  ]);
}
const headers = (i,x) => label(x,109,27,String(i+1).padStart(2,'0'),accent,700,2)+
  label(x,150,30,marks[i].title)+label(x,180,15,marks[i].note,main,400);
await save('concept-comparison',svg(1260,610,rect(0,0,1260,610,dark)+
  label(36,53,32,'STOCKFOOL  /  LOGO REVIEW',light,700,2)+
  marks.map(({art},i)=>{
    const x=36+i*402;
    return rect(x,78,384,492,'#172820',14)+group(`translate(${x+20} 0)`,headers(i,0))+
      group(`translate(${x+65} 206) scale(2)`,art())+
      rect(x+20,491,344,1,main)+label(x+20,528,18,tagline,accent,400);
  }).join('')));
