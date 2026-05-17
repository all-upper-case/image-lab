const els = {
  form: document.getElementById('generate-form'),
  provider: document.getElementById('provider'),
  model: document.getElementById('model'),
  customModel: document.getElementById('custom_model'),
  prompt: document.getElementById('prompt'),
  negativePrompt: document.getElementById('negative_prompt'),
  count: document.getElementById('count'),
  aspectRatio: document.getElementById('aspect_ratio'),
  outputFormat: document.getElementById('output_format'),
  width: document.getElementById('width'),
  height: document.getElementById('height'),
  seed: document.getElementById('seed'),
  safety: document.getElementById('safety'),
  generateButton: document.getElementById('generate-button'),
  providerStatus: document.getElementById('provider-status'),
  jobStatus: document.getElementById('job-status'),
  currentRun: document.getElementById('current-run'),
  history: document.getElementById('history'),
  refreshHistory: document.getElementById('refresh-history'),
};

let modelCatalog = {};
let pollTimer = null;
let currentRunData = null;

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }
  return data;
}

function selectedModel() {
  const custom = els.customModel.value.trim();
  return custom || els.model.value;
}

function updateModelDropdown() {
  const provider = els.provider.value;
  const models = modelCatalog[provider] || [];
  els.model.innerHTML = models
    .map(model => `<option value="${escapeHtml(model.id)}">${escapeHtml(model.label || model.id)}</option>`)
    .join('');
}

async function loadProviders() {
  const data = await fetchJson('/api/providers');
  const parts = Object.entries(data).map(([name, info]) => {
    const status = info.configured ? 'ready' : 'missing key';
    return `${name}: ${status}`;
  });
  els.providerStatus.textContent = parts.join(' · ');
}

async function loadModels() {
  modelCatalog = await fetchJson('/api/models');
  updateModelDropdown();
}

function setBusy(isBusy) {
  els.generateButton.disabled = isBusy;
  els.generateButton.textContent = isBusy ? 'Generating…' : 'Generate';
}

function payloadFromForm() {
  return {
    provider: els.provider.value,
    model: selectedModel(),
    prompt: els.prompt.value.trim(),
    negative_prompt: els.negativePrompt.value.trim(),
    count: Number(els.count.value || 1),
    aspect_ratio: els.aspectRatio.value,
    output_format: els.outputFormat.value,
    width: els.width.value ? Number(els.width.value) : null,
    height: els.height.value ? Number(els.height.value) : null,
    seed: els.seed.value ? Number(els.seed.value) : null,
    safety: els.safety.checked,
  };
}

function fillFormFromRun(run, options = {}) {
  els.provider.value = run.provider || 'venice';
  updateModelDropdown();

  const modelExists = Array.from(els.model.options).some(option => option.value === run.model);
  if (modelExists) {
    els.model.value = run.model;
    els.customModel.value = '';
  } else {
    els.customModel.value = run.model || '';
  }

  const settings = run.settings || {};
  els.prompt.value = run.prompt || settings.prompt || '';
  els.negativePrompt.value = run.negative_prompt || settings.negative_prompt || '';
  els.count.value = String(settings.count || 1);
  els.aspectRatio.value = settings.aspect_ratio || '1:1';
  els.outputFormat.value = settings.output_format || 'jpeg';
  els.width.value = settings.width || '';
  els.height.value = settings.height || '';
  els.seed.value = options.clearSeed ? '' : (settings.seed || '');
  els.safety.checked = settings.safety !== false;
}

async function submitGeneration(event) {
  event.preventDefault();
  const payload = payloadFromForm();
  await enqueueGeneration('/api/generate', payload);
}

async function enqueueGeneration(url, payload) {
  clearInterval(pollTimer);
  setBusy(true);
  els.jobStatus.textContent = 'Queued';
  els.jobStatus.className = 'job-status';
  els.currentRun.className = 'image-grid empty';
  els.currentRun.textContent = 'Waiting for provider response…';

  try {
    const data = await fetchJson(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    pollJob(data.job_id);
  } catch (error) {
    setBusy(false);
    els.jobStatus.textContent = 'Failed';
    els.jobStatus.className = 'job-status error';
    els.currentRun.className = 'empty error';
    els.currentRun.textContent = error.message;
  }
}

function pollJob(jobId) {
  pollTimer = setInterval(async () => {
    try {
      const data = await fetchJson(`/api/jobs/${jobId}`);
      const status = data.job.status;
      els.jobStatus.textContent = status;

      if (status === 'completed') {
        clearInterval(pollTimer);
        setBusy(false);
        els.jobStatus.className = 'job-status success';
        renderCurrentRun(data.run);
        loadHistory();
      } else if (status === 'failed') {
        clearInterval(pollTimer);
        setBusy(false);
        els.jobStatus.className = 'job-status error';
        els.currentRun.className = 'empty error';
        els.currentRun.textContent = data.job.error || data.run?.error || 'Generation failed.';
        loadHistory();
      }
    } catch (error) {
      clearInterval(pollTimer);
      setBusy(false);
      els.jobStatus.className = 'job-status error';
      els.jobStatus.textContent = 'Polling failed';
      els.currentRun.className = 'empty error';
      els.currentRun.textContent = error.message;
    }
  }, 1200);
}

function renderCurrentRun(run) {
  currentRunData = run;
  if (!run || !run.images?.length) {
    els.currentRun.className = 'image-grid empty';
    els.currentRun.textContent = 'No images saved for this run.';
    return;
  }
  els.currentRun.className = 'image-grid';
  els.currentRun.innerHTML = run.images.map(image => imageCardHtml(image, run)).join('');
}

function imageCardHtml(image, run) {
  const dimensions = image.width && image.height ? `${escapeHtml(image.width)} × ${escapeHtml(image.height)}` : 'Saved locally';
  const metadata = escapeHtml(JSON.stringify(image.metadata || {}, null, 2));
  const favoriteLabel = image.favorite ? '★ Favorited' : '☆ Favorite';

  return `
    <article class="image-card" data-image-id="${escapeHtml(image.id)}">
      <a href="${escapeHtml(image.local_path)}" target="_blank" rel="noreferrer">
        <img src="${escapeHtml(image.local_path)}" alt="Generated image">
      </a>
      <div class="image-card-body">
        <div class="meta">
          ${image.seed ? `Seed: ${escapeHtml(image.seed)}<br>` : ''}
          ${dimensions}
        </div>
        <div class="button-row">
          <a class="small-button" href="${escapeHtml(image.local_path)}" download>Download</a>
          <button class="small-button" type="button" data-action="favorite-image" data-image-id="${escapeHtml(image.id)}" data-favorite="${image.favorite ? '0' : '1'}">${favoriteLabel}</button>
          <button class="small-button danger-button" type="button" data-action="delete-image" data-image-id="${escapeHtml(image.id)}">Delete</button>
        </div>
        <details class="metadata-box">
          <summary>Metadata</summary>
          <pre>${metadata}</pre>
        </details>
      </div>
    </article>
  `;
}

async function loadHistory() {
  try {
    const data = await fetchJson('/api/history');
    const runs = data.runs || [];
    if (!runs.length) {
      els.history.className = 'history-list empty';
      els.history.textContent = 'No saved runs yet.';
      return;
    }
    els.history.className = 'history-list';
    els.history.innerHTML = runs.map(runCardHtml).join('');
  } catch (error) {
    els.history.className = 'history-list empty error';
    els.history.textContent = error.message;
  }
}

function runCardHtml(run) {
  const thumbs = (run.images || []).slice(0, 5).map(image => `<img src="${escapeHtml(image.local_path)}" alt="Generated thumbnail">`).join('');
  const runJson = escapeHtml(JSON.stringify(run));
  return `
    <article class="run-card" data-run-id="${escapeHtml(run.id)}">
      ${thumbs ? `<div class="run-thumbs">${thumbs}</div>` : ''}
      <div class="run-card-body">
        <div class="meta">${escapeHtml(run.provider)} · ${escapeHtml(run.model)} · ${escapeHtml(run.status)} · ${escapeHtml(run.created_at)}</div>
        <p class="prompt-preview">${escapeHtml(run.prompt)}</p>
        ${run.error ? `<div class="error">${escapeHtml(run.error)}</div>` : ''}
        <div class="button-row">
          <button class="small-button" type="button" data-action="load-run" data-run="${runJson}">Load</button>
          <button class="small-button" type="button" data-action="rerun" data-run-id="${escapeHtml(run.id)}">Rerun</button>
          <button class="small-button" type="button" data-action="vary" data-run-id="${escapeHtml(run.id)}">Vary</button>
          <button class="small-button danger-button" type="button" data-action="delete-run" data-run-id="${escapeHtml(run.id)}">Delete</button>
        </div>
        <details class="metadata-box">
          <summary>Run settings</summary>
          <pre>${escapeHtml(JSON.stringify(run.settings || {}, null, 2))}</pre>
        </details>
      </div>
    </article>
  `;
}

async function handleDocumentClick(event) {
  const target = event.target.closest('[data-action]');
  if (!target) {
    return;
  }

  const action = target.dataset.action;

  try {
    if (action === 'favorite-image') {
      const imageId = target.dataset.imageId;
      const favorite = target.dataset.favorite === '1';
      await fetchJson(`/api/images/${imageId}/favorite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ favorite }),
      });
      await refreshVisibleRun();
      await loadHistory();
    }

    if (action === 'delete-image') {
      const imageId = target.dataset.imageId;
      if (!confirm('Delete this image from the app and local generated files?')) {
        return;
      }
      await fetchJson(`/api/images/${imageId}`, { method: 'DELETE' });
      await refreshVisibleRun();
      await loadHistory();
    }

    if (action === 'delete-run') {
      const runId = target.dataset.runId;
      if (!confirm('Delete this whole run and its generated image files?')) {
        return;
      }
      await fetchJson(`/api/runs/${runId}`, { method: 'DELETE' });
      if (currentRunData?.id === runId) {
        currentRunData = null;
        els.currentRun.className = 'image-grid empty';
        els.currentRun.textContent = 'Deleted current run.';
      }
      await loadHistory();
    }

    if (action === 'rerun') {
      const runId = target.dataset.runId;
      await enqueueGeneration(`/api/runs/${runId}/rerun`, { vary: false });
    }

    if (action === 'vary') {
      const runId = target.dataset.runId;
      await enqueueGeneration(`/api/runs/${runId}/rerun`, { vary: true });
    }

    if (action === 'load-run') {
      const run = JSON.parse(target.dataset.run);
      fillFormFromRun(run);
      renderCurrentRun(run);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  } catch (error) {
    alert(error.message);
  }
}

async function refreshVisibleRun() {
  if (!currentRunData?.id) {
    return;
  }

  const data = await fetchJson(`/api/runs/${currentRunData.id}`);
  renderCurrentRun(data.run);
}

els.provider.addEventListener('change', updateModelDropdown);
els.form.addEventListener('submit', submitGeneration);
els.refreshHistory.addEventListener('click', loadHistory);
document.addEventListener('click', handleDocumentClick);

Promise.all([loadProviders(), loadModels(), loadHistory()]).catch(error => {
  els.providerStatus.textContent = error.message;
  els.providerStatus.className = 'provider-status error';
});
