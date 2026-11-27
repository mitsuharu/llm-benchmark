const select = document.querySelector('#version');
const rows = document.querySelector('#rows');
const status = document.querySelector('#status');
const search = document.querySelector('#search');
const sort = document.querySelector('#sort');
const bars = document.querySelector('#bars');
const fmt = n => Number.isFinite(n) ? n.toFixed(2) : '—';
const quality = r => r.scored === r.total && r.total > 0 ? r.score : null;
const numberOrder = (a,b) => (Number.isFinite(b)?b:-Infinity)-(Number.isFinite(a)?a:-Infinity);
fetch('data.json').then(r=>{if(!r.ok)throw Error('data');return r.json()}).then(data=>{
 for(const v of data.versions){const o=document.createElement('option');o.value=v;o.textContent=v;select.append(o)}
 function render(){
  rows.replaceChildren();bars.replaceChildren();
  const q=search.value.trim().toLowerCase();
  const runs=data.runs.filter(r=>r.version===select.value && [r.model,r.quantization,r.gpu,r.runtime].some(v=>String(v??'').toLowerCase().includes(q)));
  runs.sort((a,b)=>sort.value==='speed'?numberOrder(a.speed,b.speed):sort.value==='score'?numberOrder(quality(a),quality(b)):a.model.localeCompare(b.model));
  status.textContent=runs.length ? runs.length+' runs' : '該当する測定結果はありません';
  const measured=runs.filter(r=>Number.isFinite(r.speed)&&r.speed>=0);
  const max=Math.max(1,...measured.map(r=>r.speed));
  if(!measured.length)bars.textContent='速度の測定結果はありません';
  for(const r of measured){
   const line=document.createElement('div');line.className='bar';
   const label=document.createElement('span');label.textContent=[r.model,r.gpu,r.quantization,r.id].filter(Boolean).join(' / ');
   const meter=document.createElement('meter');meter.min=0;meter.max=max;meter.value=r.speed;meter.setAttribute('aria-label',label.textContent);
   const value=document.createElement('span');value.textContent=fmt(r.speed)+' tok/s';line.append(label,meter,value);bars.append(line);
  }
  for(const r of runs){
   const tr=document.createElement('tr');
   for(const value of [r.model,r.quantization,r.gpu,r.runtime,r.scored+' / '+r.total,fmt(r.score),fmt(r.creative),fmt(r.speed)]){
    const td=document.createElement('td');td.textContent=value??'—';tr.append(td);
   }
   const link=document.createElement('a');
   link.href='run.html?'+new URLSearchParams({version:r.version,id:r.id});
   link.textContent='詳細';
   link.setAttribute('aria-label',r.model+' の詳細（'+r.id+'）');
   const td=document.createElement('td');td.append(link);tr.append(td);rows.append(tr);
  }
 }
 select.addEventListener('change',render);sort.addEventListener('change',render);search.addEventListener('input',render);render();
}).catch(()=>{status.textContent='データの読み込みに失敗しました'});
