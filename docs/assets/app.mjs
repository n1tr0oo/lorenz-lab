import { defaults, validate } from './solver.mjs';
const $ = id => document.getElementById(id);
const form = $('config-form');
let result = null, worker = null, timer = null;
const fields = ['sigma','rho','beta','duration','transient','x0','y0','z0'];
function config() {
  return validate({ sigma: Number($('sigma').value), rho: Number($('rho').value),
    beta: Number($('beta').value), duration: Number($('duration').value),
    transient: Number($('transient').value),
    initial: ['x0','y0','z0'].map(id => Number($(id).value)) });
}
function populate(c) {
  for (const key of ['sigma','rho','beta','duration','transient']) $(key).value = c[key];
  ['x0','y0','z0'].forEach((id, i) => $(id).value = c.initial[i]);
}
function busy(value) {
  fields.forEach(id => $(id).disabled = value);
  $('preset').disabled = value; $('reset').disabled = value;
  $('run').disabled = value; $('cancel').disabled = !value;
  $('run').firstChild.textContent = value ? 'Выполняется расчёт… ' : 'Рассчитать ';
  $('download-csv').disabled = value || !result;
  $('download-json').disabled = value || !result;
  document.querySelector('.results').setAttribute('aria-busy', String(value));
}
function stop() {
  if (worker) worker.terminate();
  worker = null; clearTimeout(timer); timer = null; busy(false);
}
function failure(message) {
  stop(); $('error').textContent = message; $('error').hidden = false;
  $('status').textContent = result ? 'Расчёт не завершён. Показан предыдущий результат.' : 'Расчёт не завершён.';
}
function calculate(event) {
  if (event) event.preventDefault();
  if (!form.reportValidity()) return;
  let c;
  try { c = config(); } catch (e) { failure(e.message); return; }
  stop(); $('error').hidden = true; busy(true);
  $('status').textContent = 'Выполняется расчёт траектории…';
  try { worker = new Worker(new URL('./worker.mjs', import.meta.url), { type: 'module' }); }
  catch { failure('Не удалось запустить расчёт в браузере. Перезагрузите страницу.'); return; }
  worker.onmessage = ({ data }) => {
    if (!data.ok) { failure(data.error); return; }
    result = data.result; stop(); render();
    $('status').textContent = 'Расчёт завершён';
    $('sample-count').textContent = `${result.samples.toLocaleString('ru-RU')} отсчётов`;
    const c = result.config;
    $('run-caption').textContent = `σ = ${number(c.sigma)} · ρ = ${number(c.rho)} · β = ${number(c.beta)} · t = 0…${number(c.duration)}`;
  };
  worker.onerror = () => failure('Расчёт прерван. Попробуйте меньшую длительность.');
  timer = setTimeout(() => failure('Превышено время расчёта (8 секунд). Уменьшите длительность или измените параметры.'), 8000);
  worker.postMessage(c);
}
function number(v) { return Number(v.toPrecision(5)).toLocaleString('ru-RU'); }
function node(tag, attrs = {}, text = null) {
  const e = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [k,v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  if (text !== null) e.textContent = text;
  return e;
}
function range(values) {
  let lo = Infinity, hi = -Infinity;
  for (const v of values) { lo = Math.min(lo,v); hi = Math.max(hi,v); }
  const pad = Math.max((hi-lo)*0.08, Math.max(Math.abs(lo), Math.abs(hi), 1)*0.03);
  return [lo-pad,hi+pad];
}
function chart(svg, xr, yr, height, xlabel, ylabel) {
  svg.replaceChildren();
  const margin = { left: 55, right: 18, top: 17, bottom: 43 };
  const w = 760-margin.left-margin.right, h = height-margin.top-margin.bottom;
  const sx = v => margin.left+(v-xr[0])/(xr[1]-xr[0])*w;
  const sy = v => margin.top+h-(v-yr[0])/(yr[1]-yr[0])*h;
  for (let i=0;i<=5;i++) {
    const x=xr[0]+(xr[1]-xr[0])*i/5, y=yr[0]+(yr[1]-yr[0])*i/5;
    svg.append(node('line',{x1:sx(x),y1:margin.top,x2:sx(x),y2:margin.top+h,stroke:'#ececea','stroke-width':1}));
    svg.append(node('line',{x1:margin.left,y1:sy(y),x2:margin.left+w,y2:sy(y),stroke:'#ececea','stroke-width':1}));
    svg.append(node('text',{x:sx(x),y:margin.top+h+21,'text-anchor':'middle',fill:'#757575','font-size':11},number(x)));
    svg.append(node('text',{x:margin.left-10,y:sy(y)+4,'text-anchor':'end',fill:'#757575','font-size':11},number(y)));
  }
  svg.append(node('line',{x1:margin.left,y1:margin.top+h,x2:margin.left+w,y2:margin.top+h,stroke:'#bcbcbc','stroke-width':1}));
  svg.append(node('line',{x1:margin.left,y1:margin.top,x2:margin.left,y2:margin.top+h,stroke:'#bcbcbc','stroke-width':1}));
  svg.append(node('text',{x:margin.left+w/2,y:height-5,'text-anchor':'middle',fill:'#454545','font-family':'Times New Roman','font-size':14},xlabel));
  svg.append(node('text',{x:13,y:margin.top+h/2,'text-anchor':'middle',fill:'#454545','font-family':'Times New Roman','font-size':14,transform:`rotate(-90 13 ${margin.top+h/2})`},ylabel));
  return { sx, sy };
}
function path(svg, xs, ys, scales, dash = '', width = 1.05) {
  const d = xs.map((v,i) => `${i?'L':'M'}${scales.sx(v).toFixed(2)},${scales.sy(ys[i]).toFixed(2)}`).join(' ');
  const attrs = { d,fill:'none',stroke:'#202020','stroke-width':width,'stroke-linejoin':'round','stroke-linecap':'round' };
  if (dash) attrs['stroke-dasharray'] = dash;
  svg.append(node('path',attrs));
}
function render() {
  if (!result) return;
  const rows=[];
  for (let i=0;i<result.values.length;i+=4) {
    if (result.values[i]+1e-12>=result.config.transient) rows.push(Array.from(result.values.subarray(i,i+4)));
  }
  const [a,b] = $('projection').value.split(',').map(Number);
  const labels=['t','x','y','z'];
  const x=rows.map(v=>v[a]), y=rows.map(v=>v[b]);
  const phase=$('phase-chart');
  const scales=chart(phase,range(x),range(y),390,labels[a],labels[b]);
  path(phase,x,y,scales);
  phase.append(node('circle',{cx:scales.sx(x.at(-1)),cy:scales.sy(y.at(-1)),r:3,fill:'#171717'}));
  phase.setAttribute('aria-label',`Фазовый портрет: ${labels[a]} по горизонтали, ${labels[b]} по вертикали. Параметры sigma ${result.config.sigma}, rho ${result.config.rho}, beta ${result.config.beta}.`);
  const t=rows.map(v=>v[0]);
  const coords=[1,2,3].map(i=>rows.map(v=>v[i]));
  const time=$('time-chart');
  const st=chart(time,[t[0],t.at(-1)===t[0]?t[0]+0.01:t.at(-1)],range(coords.flat()),250,'t','x, y, z');
  coords.forEach((ys,i)=>path(time,t,ys,st,['','6 4','1 4'][i],i===2?1.5:1));
}
function download(text, name, type) {
  const url=URL.createObjectURL(new Blob([text],{type}));
  const a=document.createElement('a'); a.href=url; a.download=name;
  document.body.append(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function csv() {
  const lines=['t,x,y,z'];
  for (let i=0;i<result.values.length;i+=4)
    lines.push(Array.from(result.values.subarray(i,i+4),v=>v.toPrecision(17)).join(','));
  return lines.join('\n')+'\n';
}
form.addEventListener('submit',calculate);
form.addEventListener('input',()=>{
  if (worker) return;
  $('status').textContent='Параметры изменены. Нажмите «Рассчитать».';
  $('error').hidden=true;
});
$('preset').addEventListener('change',()=>{
  const rho={classic:28,rho10:10,rho05:0.5}[$('preset').value];
  populate({...defaults,rho}); calculate();
});
$('reset').addEventListener('click',()=>{ $('preset').value='classic'; populate(defaults); calculate(); });
$('cancel').addEventListener('click',()=>{
  stop(); $('status').textContent=result?'Расчёт отменён. Показан предыдущий результат.':'Расчёт отменён.';
});
$('projection').addEventListener('change',render);
$('download-csv').addEventListener('click',()=>{ if(result) download(csv(),'lorenz_trajectory.csv','text/csv;charset=utf-8'); });
$('download-json').addEventListener('click',async()=>{
  if(!result) return;
  const snapshot=result;
  const data=csv();
  const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(data));
  const sha=Array.from(new Uint8Array(digest),v=>v.toString(16).padStart(2,'0')).join('');
  const manifest={schema_version:1,created_utc:new Date().toISOString(),config:snapshot.config,
    solver:'RK4',internal_step:snapshot.step,effective_sample_step:snapshot.effective_sample_step,
    samples:snapshot.samples,rhs_evaluations:snapshot.evaluations,
    transient_applies_to:'plots only; CSV retains every sample',
    numerical_environment:'JavaScript Float64 in the browser',csv_sha256:sha};
  download(JSON.stringify(manifest,null,2)+'\n','lorenz_run.json','application/json');
});
window.addEventListener('pagehide',stop);
calculate();
