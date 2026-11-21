import {Composition,registerRoot,staticFile} from 'remotion';
import {Film} from './Film';
import {projects} from './projects';
import {timeline} from './storyboard';

registerRoot(() => <>{projects.map(project =>
  <Composition key={project.id} id={project.id} component={Film}
    defaultProps={{project,assetBase:staticFile('placeholder').replace(/placeholder$/,'')}}
    width={project.width} height={project.height} fps={project.fps}
    durationInFrames={timeline(project).at(-1)!.end}/>)}</>);
