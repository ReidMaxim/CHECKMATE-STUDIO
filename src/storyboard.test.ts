import test from 'node:test';
import assert from 'node:assert/strict';
import input from '../projects/legal-mate.json';
import {boardPoint,cameraPose,storyboard,timeline} from './storyboard';

test('sample contract and distribution format',() => {
  const parsed = storyboard.parse(input);
  assert.deepEqual([parsed.width,parsed.height,parsed.fps],[1080,1920,30]);
  assert.equal(storyboard.safeParse({...input,fps:25}).success,false);
});
test('contiguous timeline totals 41 seconds',() => {
  const shots = timeline(storyboard.parse(input));
  assert.deepEqual(shots.map(entry=>entry.start),[0,180,390,540,690,840,960]);
  assert.equal(shots.at(-1)?.end,1230);
});
test('overlapping captions, negative timing and unsupported presets fail',() => {
  const invalid = structuredClone(input);
  invalid.scenes[0].captions[1].from = 40;
  assert.equal(storyboard.safeParse(invalid).success,false);
  for (const overrides of [{frames:-1},{preset:'invented'},{camera:{focus:'i8',zoom:3}},{moveFrames:180},{moveAt:5},{moveAt:175,moveFrames:6}]) {
    assert.equal(storyboard.safeParse({...input,scenes:[{...input.scenes[0],...overrides}]}).success,false);
  }
});
test('camera offsets obey zoom bounds and orientation',() => {
  assert.deepEqual(boardPoint('a8','black'),[7,7]);
  const white = cameraPose({focus:'a8',zoom:1.2},'white');
  const black = cameraPose({focus:'a8',zoom:1.2},'black');
  assert.ok(white.x > 0 && white.y > 0 && white.x <= .8);
  assert.equal(black.x,-white.x);
  assert.equal(black.y,-white.y);
  const full = cameraPose({focus:null,zoom:1},'white');
  assert.deepEqual(full,{x:0,y:0,zoom:1});
});
