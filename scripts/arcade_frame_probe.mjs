import {existsSync} from 'node:fs';
import {mkdir} from 'node:fs/promises';
import {bundle} from '@remotion/bundler';
import {renderMedia,renderStill,selectComposition} from '@remotion/renderer';

const browserExecutable = process.env.CHROMIUM_BIN ??
  ['/usr/bin/chromium','/usr/bin/google-chrome'].find(path => existsSync(path));
const chromiumOptions = {gl:'swangle'};
const serveUrl = await bundle({entryPoint:'src/arcade-remotion.tsx'});
const directory = 'out/arcade-frames';
await mkdir(directory,{recursive:true});
const options = {serveUrl,browserExecutable,chromiumOptions};

if (process.argv[2] === 'arcade-chess-impact') {
  const composition = await selectComposition({...options,id:'arcade-chess-impact'});
  await renderStill({...options,composition,frame:250,output:`${directory}/impact-source-250.png`});
  // Retain the before/after modes for diagnosis. Both use the same Chromium and encoding options.
  for (const disableSharedMemoryCapture of [false,true]) {
    const mode = disableSharedMemoryCapture?'regular':'shared';
    await renderMedia({...options,composition,frameRange:[231,269],codec:'h264',
      pixelFormat:'yuv420p',colorSpace:'bt709',crf:18,concurrency:3,disableSharedMemoryCapture,
      outputLocation:`${directory}/impact-${mode}-capture-window.mp4`});
  }
} else {
  const composition = await selectComposition({...options,id:'arcade-chess-battle'});
  for (const [name,frame] of [['queen-cinematic',91],['mate-cinematic',315],['final-board',400]]) {
    await renderStill({...options,composition,frame,output:`${directory}/${name}.png`});
  }
}
