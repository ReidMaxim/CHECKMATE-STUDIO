import raw from './generated.json';
import {loadProject} from './storyboard';
export const projects = raw.map(loadProject);
