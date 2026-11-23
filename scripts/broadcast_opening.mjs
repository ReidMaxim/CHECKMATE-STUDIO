import {join} from 'node:path';
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';

const [output, variant] = process.argv.slice(2);
const serveUrl = await bundle({entryPoint:'src/remotion.tsx'});
const browserExecutable = process.env.CHROMIUM_BIN;
const chromiumOptions = {gl:'swangle'};
const composition = await selectComposition({serveUrl,id:'unseen-documentary',browserExecutable,chromiumOptions});
await renderMedia({composition,serveUrl,browserExecutable,chromiumOptions,codec:'h264',audioCodec:'aac',
  pixelFormat:'yuv420p',frameRange:[0,89],scale:.5,disableSharedMemoryCapture:true,
  outputLocation:join(output,`opening-${variant}.mp4`)});
