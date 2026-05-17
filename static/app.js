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

async function submitGeneration(event) {
  event.preventDefault();
  clearInterval(pollTimer);
  setBusy(true);
  els.jobStatus.textContent = 'Queued';
  els.jobStatus.className = 'job-status';
  els.currentRun.className = 'image-grid empty';
  els.currentRun.textContent = 'Waiting for provider response…';

  try {
    const data = await fetchJson('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payloadFromForm()),
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
  if (!run || !run.images?.length) {
    els.currentRun.className = 'image-grid empty';
    els.currentRun.textContent = 'No images saved for this run.';
    return;
  }
  els.currentRun.className = 'image-grid';
  els.currentRun.innerHTML = run.images.map(imageCardHtml).join('');
}

function imageCardHtml(image) {
  return `
    <article class="image-card">
      <a href="${escapeHtml(image.local_path)}" target="_blank" rel="noreferrer">
        <img src="${escapeHtml(image.local_path)}" alt="Generated image">
      </a>
      <div class="image-card-body">
        <div class="meta">
          ${image.seed ? `Seed: ${escapeHtml(image.seed)}<br>` : ''}
          ${image.width && image.height ? `${escapeHtml(image.width)} × ${escapeHtml(image.height)}` : 'Saved locally'}
        </div>
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
  return `
    <article class="run-card">
      ${thumbs ? `<div class="run-thumbs">${thumbs}</div>` : ''}
      <div class="run-card-body">
        <div class="meta">${escapeHtml(run.provider)} · ${escapeHtml(run.model)} · ${escapeHtml(run.status)} · ${escapeHtml(run.created_at)}</div>
        <p class="prompt-preview">${escapeHtml(run.prompt)}</p>
        ${run.error ? `<div class="error">${escapeHtml(run.error)}</div>` : ''}
      </div>
    </article>
  `;
}

els.provider.addEventListener('change', updateModelDropdown);
els.form.addEventListener('submit', submitGeneration);
els.refreshHistory.addEventListener('click', loadHistory);

Promise.all([loadProviders(), loadModels(), loadHistory()]).catch(error => {
  els.providerStatus.textContent = error.message;
  els.providerStatus.className = 'provider-status error';
});
