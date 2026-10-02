import fs from 'node:fs';
import { simulate } from '../docs/assets/solver.mjs';
const {config,maxStep}=JSON.parse(fs.readFileSync(0,'utf8'));
const r=simulate(config,maxStep);
process.stdout.write(JSON.stringify({values:Array.from(r.values),step:r.step,samples:r.samples}));
