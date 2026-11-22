const select = document.querySelector('#version');
const rows = document.querySelector('#rows');
const status = document.querySelector('#status');
const fmt = n => Number.isFinite(n) ? n.toFixed(2) : '—';
fetch('data.json').then(r=>{if(!r.ok)throw Error('data');return r.json()}).then(data=>{
 for(const v of data.versions){const o=document.createElement('option');o.value=v;o.textContent=v;select.append(o)}
 function render(){rows.replaceChildren();const runs=data.runs.filter(r=>r.version===select.value);status.textContent=runs.length ? runs.length+' runs' : '測定結果はまだありません';
 for(const r of runs){const tr=document.createElement('tr');for(const value of [r.model,r.quantization,r.gpu,r.runtime,r.scored+' / '+r.total,fmt(r.score),fmt(r.creative),fmt(r.speed),r.id]){const td=document.createElement('td');td.textContent=value??'—';tr.append(td)} rows.append(tr)}}
 select.addEventListener('change',render);render();
}).catch(()=>{status.textContent='データの読み込みに失敗しました'});
