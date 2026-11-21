import React, {useRef, useState, type ReactNode} from 'react';
import {createRoot} from 'react-dom/client';
import {Player, type PlayerRef} from '@remotion/player';
import {Film} from './Film';
import {projects} from './projects';
import {timeline} from './storyboard';
import './studio.css';

const workflows = 'https://github.com/ReidMaxim/CHECKMATE-STUDIO/actions/workflows/';

class ErrorBoundary extends React.Component<{children:ReactNode},{error?:Error}> {
  state:{error?:Error} = {};
  static getDerivedStateFromError(error:Error) {return {error};}
  render() {
    return this.state.error ? <main className="studio-error"><h1>Screening room unavailable</h1><p>{this.state.error.message}</p>
      <button onClick={() => window.location.reload()}>Reload studio</button></main> : this.props.children;
  }
}

function Studio() {
  const [id,setId] = useState(projects[0]?.id ?? '');
  const [flipped,setFlipped] = useState(false);
  const [narration,setNarration] = useState(true);
  const player = useRef<PlayerRef>(null);
  const project = projects.find(item => item.id===id);
  const shots = project ? timeline(project) : [];
  const director = project?.presentation === 'director';
  const workflow = workflows + (director ? 'directors-cut.yml' : 'render.yml');
  const artifact = director ? 'directors-cut' : 'sample-video';
  const footerTime = (frames:number) => new Intl.NumberFormat('en-US',{minimumIntegerDigits:2}).format(Math.floor(frames/(project?.fps ?? 30)));
  function jumpTo(frame:number) {
    const instance=player.current;
    instance?.pause();
    instance?.seekTo(frame);
    document.getElementById('screening')?.scrollIntoView({block:'nearest',behavior:'smooth'});
  }
  return <>
    <header className="mast"><div className="brand"><span className="brand-mark" aria-hidden="true">♞</span>
      <strong>CHECKMATE<b>//</b>STUDIO</strong></div><a href={workflow}>Render workflow ↗</a></header>
    <main className="studio">
      <div className="heading"><h1>Screening room</h1><p>Review the film, inspect each shot, and download completed cloud renders.</p></div>
      {project ? <div className="workspace">
        <section className="panel screening" id="screening" aria-label="Video preview">
          <div className="panel-heading"><h2>Film preview</h2><span>9:16 · 00:{footerTime(shots.at(-1)!.end)}</span></div>
          <div className="player-frame">
            <Player key={id} ref={player} component={Film} inputProps={{project,flipped,narration,assetBase:import.meta.env.BASE_URL}}
              compositionWidth={project.width} compositionHeight={project.height} fps={project.fps} durationInFrames={shots.at(-1)!.end}
              style={{width:'100%',aspectRatio:'9/16'}} controls
              errorFallback={() => <p className="player-error">Preview playback failed. Reload the page to retry.</p>}/>
          </div>
        </section>
        <div className="sidebar">
          <section className="panel details">
            <label htmlFor="project">Project</label>
            <select id="project" value={id} onChange={event => {setId(event.target.value);setFlipped(false);}}>
              {projects.map(item => <option value={item.id} key={item.id}>{item.title}</option>)}
            </select>
            <p className="series">{project.series}</p>
            <h2>{project.title}</h2><p>{project.summary}</p>
            <details><summary>PGN and sources</summary>
              {project.sources.map(source => <p key={source.url}><a href={source.url}>{source.label} ↗</a></p>)}
              <pre>{project.pgn || project.fen}</pre>
            </details>
          </section>
          <section className="panel details"><h2>Storyboard</h2>
            <ol className="shots">{shots.map(({scene,start},index) =>
              <li key={start}><button onClick={() => jumpTo(start)} aria-label={`Seek to ${scene.title}`}>
                <span className="shot-number">{String(index+1).padStart(2,'0')}</span><span>{scene.title}</span><time>00:{footerTime(start)}</time>
              </button></li>)}</ol>
          </section>
          <section className="panel details">
            <h2>Preview settings</h2>
            <label className="check"><input type="checkbox" checked={flipped} onChange={event => setFlipped(event.target.checked)}/> Flip board</label>
            <label className="check"><input type="checkbox" checked={narration} onChange={event => setNarration(event.target.checked)}/> Narration</label>
            <p className="muted">{project.width} × {project.height} · {project.fps} fps · H.264 / AAC</p>
          </section>
          <section className="panel details"><h2>Cloud renders</h2>
            <p>Open a successful workflow run and download <strong>{artifact}</strong> from its Artifacts section.</p>
            <a className="action" href={workflow}>View render runs ↗</a>
          </section>
        </div>
      </div> : <p className="panel details">No projects are available. Add a validated storyboard to the next build.</p>}
    </main>
  </>;
}
createRoot(document.getElementById('root')!).render(<ErrorBoundary><Studio/></ErrorBoundary>);
