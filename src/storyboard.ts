import {z} from 'zod';

const square = z.string().regex(/^[a-h][1-8]$/);
const frame = z.number().int().nonnegative();
const text = z.string().trim().min(1);
const cue = z.strictObject({from: frame, to: frame, text});
export const presets = ['establishing', 'threat', 'critical', 'variation', 'evaluation', 'suspense', 'reveal', 'final'] as const;
const scene = z.strictObject({
  preset: z.enum(presets), title: text, frames: frame.min(1), ply: frame,
  line: text.optional(), moveFrames: frame,
  camera: z.strictObject({focus: square.nullable(), zoom: z.number().min(1).max(1.35)}),
  highlights: z.array(square), arrows: z.array(z.tuple([square, square]).refine(([a,b]) => a !== b)),
  transition: z.enum(['cut', 'glide']), captions: z.array(cue), overlay: text.optional(),
  evaluation: z.strictObject({label: text, whitePercent: z.number().min(0).max(100), source: text}).optional(),
}).superRefine((value, context) => {
  if (value.moveFrames >= value.frames) context.addIssue({code:'custom',path:['moveFrames'],message:'Move must finish before scene ends'});
  let end = 0;
  value.captions.forEach((item, index) => {
    if (item.from < end || item.from >= item.to || item.to > value.frames) {
      context.addIssue({code:'custom',path:['captions',index],message:'Caption must be ordered, non-overlapping and inside its scene'});
    }
    end = item.to;
  });
  if (value.preset === 'evaluation' && !value.evaluation) context.addIssue({code:'custom',message:'Evaluation shot requires attributed engine data'});
});
export const storyboard = z.strictObject({
  version:z.literal(1), id:z.string().regex(/^[a-z][a-z0-9-]*$/), title:text,
  series:z.enum(['Chess Crimes','The Chess Lab','Chess History Files','Find the Move']), summary:text,
  sources:z.array(z.strictObject({label:text,url:z.url({protocol:/^https?$/})})).min(1),
  pgn:z.string(), fen:text.optional(), theme:z.enum(['forest','slate']), orientation:z.enum(['white','black']),
  width:z.literal(1080), height:z.literal(1920), fps:z.literal(30),
  audio:z.array(z.strictObject({asset:z.string().regex(/^[\w-]+\.(mp3|wav|m4a)$/), start:frame,
    end:frame.optional(), volume:z.number().min(0).max(1), kind:z.enum(['narration','music','effect']), label:text})),
  variations:z.record(z.string().regex(/^(?!main$)[\w-]+$/),z.strictObject({fromPly:frame,moves:z.array(text).min(1)})).optional(),
  scenes:z.array(scene).min(1),
}).superRefine((value, context) => {
  if (!value.pgn.trim() && !value.fen) context.addIssue({code:'custom',message:'Supply a PGN or FEN'});
  const duration = value.scenes.reduce((sum,item) => sum + item.frames,0);
  value.audio.forEach((track,index) => {
    if (track.start >= duration || (track.end !== undefined && (track.end <= track.start || track.end > duration))) {
      context.addIssue({code:'custom',path:['audio',index],message:'Audio interval lies outside the video'});
    }
  });
});
export type Storyboard = z.infer<typeof storyboard>;
export type Scene = Storyboard['scenes'][number];

const snapshot = z.object({
  fen:text, pieces:z.record(square,z.enum(['p','n','b','r','q','k','P','N','B','R','Q','K'])),
  legal:frame, check:square.nullable(), mate:z.boolean(),
  move:z.object({source:square,target:square,capture:square.nullable(),rook:z.tuple([square,square]).nullable(),san:text}).optional(),
});
export type Snapshot = z.infer<typeof snapshot>;
export type Project = Storyboard & {lines:Record<string, Snapshot[]>};

export function loadProject(raw: Record<string, unknown>): Project {
  const {lines, ...authored} = raw;
  return {...storyboard.parse(authored),lines:z.record(text,z.array(snapshot).min(1)).parse(lines)};
}

export function timeline(project: Storyboard) {
  let start = 0;
  return project.scenes.map((scene) => {
    const entry = {scene,start,end:start + scene.frames};
    start = entry.end;
    return entry;
  });
}

export function boardPoint(square: string, orientation: Storyboard['orientation']) {
  const x = square.charCodeAt(0) - 97;
  const y = 8 - Number(square[1]);
  return orientation === 'white' ? [x,y] : [7-x,7-y];
}

export function cameraPose(camera: Scene['camera'], orientation: Storyboard['orientation']) {
  const [file, rank] = camera.focus ? boardPoint(camera.focus, orientation) : [3.5,3.5];
  const limit = (camera.zoom - 1) * 4;
  const offset = (coordinate:number) => Math.max(-limit,Math.min(limit,(3.5-coordinate)*camera.zoom));
  return {x:offset(file),y:offset(rank),zoom:camera.zoom};
}
