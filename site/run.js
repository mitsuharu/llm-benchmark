const page = document.querySelector('#run');
const statusLine = document.querySelector('#status');
const params = new URLSearchParams(location.search);

function append(parent, tag, text) {
  const element = document.createElement(tag);
  if (text != null) element.textContent = text;
  parent.append(element);
  return element;
}

function facts(parent, entries) {
  const list = append(parent, 'dl');
  for (const [label, value] of entries) {
    append(list, 'dt', label);
    append(list, 'dd', value ?? '—');
  }
}

const fmt = (value, unit = '') => Number.isFinite(value) ? value.toFixed(2) + unit : '—';
const size = value => Number.isFinite(value) ? fmt(value / 1024 ** 3, ' GiB') : null;
const score = (value, max) => Number.isFinite(value) ? `${fmt(value)} / ${max}` : '—';

function renderEnvironment(run) {
  append(page, 'h2', '実行環境');
  const host = run.environment || {};
  const gpus = (host.detected_nvidia_gpus || []).map(gpu =>
    [gpu.name, size(gpu.vram_bytes), gpu.driver ? `ドライバー ${gpu.driver}` : null].filter(Boolean).join(' / ')
  );
  facts(page, [
    ['計測対象', run.environment_scope === 'runner_host' ? 'Runner を実行した PC' : run.environment_scope],
    ['OS / アーキテクチャ', [host.os, host.release, host.architecture].filter(Boolean).join(' ') || null],
    ['CPU', host.cpu],
    ['論理 CPU 数', host.logical_cpus],
    ['RAM', size(host.ram_bytes)],
    ['推論に使用した GPU（記録値）', run.gpu],
    ['検出された GPU', gpus.length ? gpus.map((gpu, index) => `${index + 1}. ${gpu}`).join(' ｜ ') : null],
    ['ランタイム', [run.runtime, run.runtime_version].filter(Boolean).join(' ') || null],
    ['バックエンド', run.backend],
    ['量子化', run.quantization],
    ['コンテキスト長', run.settings?.context_length],
    ['Temperature', run.settings?.temperature],
    ['出力トークン上限', run.settings?.max_tokens],
  ]);
}

function renderCase(row) {
  const section = append(page, 'details');
  append(section, 'summary', `${row.case_id} · ${row.category} · ${score(row.score, row.max_score)}`);
  append(section, 'h3', '問題文');
  append(section, 'pre', row.prompt);
  facts(section, [
    ['状態', row.status],
    ['応答時間の中央値', fmt(row.elapsed_seconds, ' 秒')],
    ['最初の本文までの中央値', fmt(row.ttft_seconds, ' 秒')],
    ['生成速度の中央値', fmt(row.generation_tokens_per_second, ' tok/s')],
  ]);
  const repetitions = row.repetitions || [];
  if (!repetitions.length) append(section, 'p', '各回の記録はありません');
  for (const [index, entry] of repetitions.entries()) {
    const number = entry.number ?? index + 1;
    const trial = append(section, 'details');
    append(trial, 'summary', `${number} 回目 · ${score(entry.score, row.max_score)}`);
    facts(trial, [
      ['状態', entry.status],
      ['応答時間', fmt(entry.elapsed_seconds, ' 秒')],
      ['最初の本文まで', fmt(entry.ttft_seconds, ' 秒')],
      ['入力 / 出力トークン数', `${entry.input_tokens ?? '—'} / ${entry.output_tokens ?? '—'}`],
      ['入力処理速度', fmt(entry.prompt_tokens_per_second, ' tok/s')],
      ['生成速度', fmt(entry.generation_tokens_per_second, ' tok/s')],
    ]);
    const answer = row.answers?.[String(number)];
    append(trial, 'h4', '回答');
    if (typeof answer === 'string') append(trial, 'pre', answer);
    else append(trial, 'p', '回答本文は未公開です');
    if (entry.rubric_items?.length) {
      append(trial, 'h4', '採点根拠');
      const reasons = append(trial, 'ol');
      for (const item of entry.rubric_items) {
        append(reasons, 'li', `評価 ${item.rating ?? '—'} · ${item.reason}`);
      }
    }
  }
}

async function load() {
  const index = await fetch('data.json');
  if (!index.ok) throw Error('index');
  const {runs} = await index.json();
  const item = runs.find(run => run.version === params.get('version') && run.id === params.get('id'));
  if (!item) {
    statusLine.textContent = '指定された計測結果が見つかりません';
    return;
  }
  const response = await fetch(item.detail);
  if (!response.ok) throw Error('run');
  const run = await response.json();
  document.querySelector('#title').textContent = run.model;
  document.title = `${run.model} | LLM Benchmark`;
  append(page, 'p', `v${item.version} · ${item.id}`);
  renderEnvironment(run);
  append(page, 'h2', '問題別の結果');
  for (const row of run.cases) renderCase(row);
  statusLine.hidden = true;
  page.hidden = false;
}

load().catch(() => { statusLine.textContent = '計測の詳細を読み込めませんでした'; });
