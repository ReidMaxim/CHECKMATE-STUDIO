import {readdirSync, readFileSync} from 'node:fs';
import {storyboard} from '../src/storyboard';
for (const file of readdirSync('projects').filter(name => name.endsWith('.json'))) {
  const result = storyboard.safeParse(JSON.parse(readFileSync('projects/'+file,'utf8')));
  if (!result.success) {
    console.error(file, result.error.issues);
    process.exitCode = 1;
  }
}
