import '@fontsource/dm-sans/latin-500.css';
import '@fontsource/dm-sans/latin-700.css';
import '@fontsource/playfair-display/latin-600.css';
import '@fontsource/noto-sans-symbols-2/index.css';
import {AbsoluteFill, Audio, Easing, interpolate, Sequence, useCurrentFrame} from 'remotion';
import {Chessboard} from './Chessboard';
import {cameraPose, timeline, type Project} from './storyboard';
import './film.css';

const ease = (value:number) => Easing.inOut(Easing.cubic)(Math.min(1,Math.max(0,value)));
export type FilmProps = {project:Project; assetBase:string; narration?:boolean; flipped?:boolean};

export function Film({project,assetBase,narration=true,flipped=false}:FilmProps) {
  const frame = useCurrentFrame();
  const entries = timeline(project);
  const index = entries.findIndex(entry => frame < entry.end);
  const {scene,start} = entries[Math.max(0,index)];
  const local = frame-start;
  const previousScene = entries[index-1]?.scene;
  const orientation = flipped ? (project.orientation==='white'?'black':'white') : project.orientation;
  const line = project.lines[scene.line ?? 'main'];
  const state = line[scene.ply];
  const move = scene.moveFrames ? ease(local/scene.moveFrames) : 1;
  const pose = cameraPose(scene.camera,orientation);
  const prior = previousScene && scene.transition==='glide' ? cameraPose(previousScene.camera,orientation) : pose;
  const blend = ease(local/27);
  const camera = {x:interpolate(blend,[0,1],[prior.x,pose.x]), y:interpolate(blend,[0,1],[prior.y,pose.y]),
    zoom:interpolate(blend,[0,1],[prior.zoom,pose.zoom])};
  const caption = scene.captions.find(cue => cue.from <= local && local < cue.to);
  const status = move < 1 ? line[scene.ply-1] : state;
  return <AbsoluteFill className="film">
    <div className="film-grid"/>
    <div className="film-kicker"><i/>{project.series.toUpperCase()}</div>
    <div className="film-title" key={index}>{scene.title}</div>
    <div className="film-board-label"><span>{scene.line ? 'VARIATION' : 'POSITION'}</span>
      <span>{status.move?.san ?? 'START'}{status.mate ? '  ·  CHECKMATE' : status.check ? '  ·  CHECK' : ''}</span></div>
    <div className="film-board">
      <div style={{transform:`translate(${camera.x*100/8}%, ${camera.y*100/8}%) scale(${camera.zoom})`}}>
        <Chessboard position={state} previous={line[scene.ply-1]} progress={move} orientation={orientation} theme={project.theme}
          highlights={scene.highlights} arrows={scene.arrows} emphasis={ease((local-(scene.moveFrames || 0))/18)}/>
      </div>
    </div>
    {scene.evaluation && <div className="film-eval"><span style={{width:`${scene.evaluation.whitePercent}%`}}/>{scene.evaluation.label} · {scene.evaluation.source}</div>}
    {scene.overlay && <div className="film-overlay">{scene.overlay}</div>}
    <div className="film-caption">{caption?.text}</div>
    <div className="film-footer"><span>CHECKMATE<span className="film-gold">//</span>STUDIO</span><span>{String(index+1).padStart(2,'0')} / {String(entries.length).padStart(2,'0')}</span></div>
    {project.audio.filter(track => narration || track.kind!=='narration').map((track, i) =>
      <Sequence key={i} from={track.start} durationInFrames={(track.end ?? entries.at(-1)!.end)-track.start} layout="none">
        <Audio src={assetBase+track.asset} volume={track.volume}/>
      </Sequence>)}
  </AbsoluteFill>;
}
