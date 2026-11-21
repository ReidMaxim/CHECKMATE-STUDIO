import {mkdir} from 'node:fs/promises';
import {existsSync} from "node:fs";
import {bundle} from '@remotion/bundler';
import {renderMedia,selectComposition} from '@remotion/renderer';

const id = process.argv[2] ?? 'legal-mate';
if (!/^[a-z][a-z0-9-]*$/.test(id)) throw new Error('Invalid composition ID');
const arcade = ['arcade-chess','arcade-chess-impact','arcade-chess-battle'].includes(id);
const serveUrl = await bundle({entryPoint:arcade ? 'src/arcade-remotion.tsx' : 'src/remotion.tsx'});
const browserExecutable = process.env.CHROMIUM_BIN ?? ['/usr/bin/chromium','/usr/bin/google-chrome'].find(path => existsSync(path));
const chromiumOptions = {gl:'swangle'};
const composition = await selectComposition({serveUrl,id,browserExecutable,chromiumOptions});
await mkdir('out',{recursive:true});
await renderMedia({composition,serveUrl,codec:'h264',audioCodec:'aac',colorSpace:'bt709',pixelFormat:'yuv420p',crf:18,
  disableSharedMemoryCapture:arcade,
  audioBitrate:'192k',enforceAudioTrack:true,browserExecutable,chromiumOptions,
  concurrency:Number(process.env.RENDER_CONCURRENCY ?? 3),outputLocation:`out/${id}.mp4`,
  onProgress:({renderedFrames,encodedFrames}) => {
    if (renderedFrames % 300===0 && renderedFrames!==0 && encodedFrames<5) console.log('Frames drawn:',renderedFrames);
  }});
