import test from 'node:test';
import assert from 'node:assert/strict';
import { defaults, derivative, simulate, validate } from '../docs/assets/solver.mjs';
const short={...defaults,duration:1,transient:0};
test('known Lorenz derivative',()=>assert.deepEqual(derivative([1,2,3],defaults),[10,23,-6]));
test('origin remains stationary',()=>assert.ok(Array.from(simulate({...short,initial:[0,0,0]}).values).filter((_,i)=>i%4!==0).every(v=>v===0)));
test('exact exponential decay',()=>{
  const r=simulate({...short,initial:[0,0,1]});
  for(let i=0;i<r.values.length;i+=4) assert.ok(Math.abs(r.values[i+3]-Math.exp(-defaults.beta*r.values[i]))<1e-10);
});
test('nonzero equilibrium remains stationary',()=>{
  const x=Math.sqrt(defaults.beta*(defaults.rho-1));const r=simulate({...short,initial:[x,x,defaults.rho-1]});
  assert.ok(Math.abs(r.values.at(-1)-(defaults.rho-1))<1e-10);
});
test('Lorenz symmetry is preserved',()=>{
  const a=simulate(short).values,b=simulate({...short,initial:[-1,-1,1]}).values;
  for(let i=0;i<a.length;i+=4){assert.ok(Math.abs(a[i+1]+b[i+1])<1e-10);assert.ok(Math.abs(a[i+2]+b[i+2])<1e-10);assert.ok(Math.abs(a[i+3]-b[i+3])<1e-10);}
});
test('both endpoints and a uniform output interval are retained',()=>{
  const r=simulate({...short,duration:1.005});assert.equal(r.values[0],0);assert.equal(r.values.at(-4),1.005);
  assert.ok(r.effective_sample_step<=0.01);
});
test('default calculation contains 3001 samples',()=>assert.equal(simulate(defaults).samples,3001));
test('nonfinite and boolean parameters are rejected',()=>{
  for(const v of [NaN,Infinity,true,'10']) assert.throws(()=>validate({...short,sigma:v}));
});
test('input bounds are enforced',()=>{
  for(const c of [{sigma:0},{rho:-1},{beta:51},{duration:51},{sample_step:0.001}]) assert.throws(()=>validate({...short,...c}));
});
test('initial state shape and coordinates are checked',()=>{
  for(const initial of [[1,2],[1,2,Infinity],[101,1,1]]) assert.throws(()=>validate({...short,initial}));
});
test('invalid transient is rejected',()=>{
  for(const transient of [-1,1,NaN]) assert.throws(()=>validate({...short,transient}));
});
test('integration budget is enforced before running',()=>assert.throws(()=>simulate(short,0.000001),/лимит/));
