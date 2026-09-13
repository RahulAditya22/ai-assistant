const $ = s => document.querySelector(s);
const status = (m, show = true) => {
  $('#status').textContent = m;
  $('#status').classList.toggle('hidden', !show);
};

async function api(url, opt = {}) {
  const r = await fetch(url, opt);
  const d = await r.json().catch(() => ({ error: `Server returned HTTP ${r.status}` }));
  if (!r.ok) throw new Error(d.error || `Request failed (${r.status})`);
  return d;
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
}

function selected() {
  return [...document.querySelectorAll('.docbox:checked')].map(x => Number(x.value));
}

async function loadDocs() {
  const docs = await api('/api/documents');
  $('#docs').innerHTML = docs.length ? docs.map(d => `
    <div class="doc"><label><input type="checkbox" class="docbox" value="${d.id}" checked>
    <span><strong>${esc(d.name)}</strong><small>${d.pages || 1} page(s) · ${Number(d.char_count || 0).toLocaleString()} chars · ${esc(d.file_type.toUpperCase())}</small></span></label></div>`).join('') : '<p style="margin-top:14px">No documents yet.</p>';
}

$('#file').addEventListener('change', () => {
  const f = $('#file').files[0];
  $('#fileLabel').textContent = f ? f.name : 'Upload PDF, TXT or DOCX';
  $('#fileHint').textContent = f ? `${(f.size / 1024 / 1024).toFixed(2)} MB · ready to process` : 'Files are extracted and indexed locally.';
});

$('#uploadForm').addEventListener('submit', async e => {
  e.preventDefault();
  const f = $('#file').files[0];
  if (!f) return status('Choose a file first.');
  if (f.size === 0) return status('The selected file is empty.');
  if (f.size > 20 * 1024 * 1024) return status('File is too large. Maximum size is 20 MB.');

  const button = $('#uploadButton');
  button.disabled = true;
  button.textContent = 'Processing…';
  status(`Uploading and processing ${f.name}…`);
  try {
    const fd = new FormData();
    fd.append('file', f, f.name);
    const d = await api('/api/upload', { method:'POST', body:fd });
    status(`Processed ${d.name}: ${d.chunks} chunks, ${d.edges} graph relationships.`);
    $('#file').value = '';
    $('#fileLabel').textContent = 'Upload another PDF, TXT or DOCX';
    $('#fileHint').textContent = 'The document is now available in the library.';
    await loadDocs();
    await graph();
  } catch (err) {
    status(`Upload failed: ${err.message}`);
  } finally {
    button.disabled = false;
    button.textContent = 'Process document';
  }
});

async function ask(q) {
  if (!q.trim()) return status('Enter a question.');
  status('Retrieving evidence and checking reasoning paths…');
  $('#answer').className = 'answer'; $('#answer').innerHTML = '';
  try {
    const d = await api('/api/ask', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({question:q, document_ids:selected()}) });
    let html = `<h3>${esc(d.answer)}</h3><div class="meta"><span class="tag">${esc(d.classification || '')}</span><span class="tag">confidence ${((d.confidence || 0)*100).toFixed(0)}%</span></div>`;
    if (d.path) html += `<div class="reason"><strong>Reasoning path</strong><br>${d.path.map(esc).join(' → ')}<br><br>${esc(d.inference || '')}</div>`;
    if (d.evidence?.length) html += '<h4>Evidence</h4>' + d.evidence.map(e => `<div class="evidence"><small>${esc(e.document_name)}${e.page ? ' · page '+e.page : ''} · score ${Number(e.score || 0).toFixed(3)}</small>${esc(e.text)}</div>`).join('');
    if (d.results?.length) html += '<h4>Top retrieval results</h4>' + d.results.map(r => `<div class="result">${esc(r.document_name)} · ${Number(r.score || 0).toFixed(3)} — ${esc(r.text.slice(0,180))}…</div>`).join('');
    $('#answer').innerHTML = html; status('', false);
  } catch (err) { status(err.message); }
}

$('#ask').addEventListener('click', () => ask($('#question').value));
$('#question').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask($('#question').value); } });
$('#summary').addEventListener('click', () => ask('Summarize the key points of these documents.'));

async function graph() {
  try {
    const d = await api('/api/graph');
    $('#graph').innerHTML = d.edges.length ? d.edges.map(e => `<span class="node">${esc(e.subject)}</span><span class="edge">— ${esc(e.relation)} →</span><span class="node">${esc(e.object)}</span>`).join('') : '<p>No relationships extracted yet.</p>';
  } catch (e) { $('#graph').textContent = e.message; }
}
$('#refreshGraph').addEventListener('click', graph);

$('#runLab').addEventListener('click', async () => {
  try {
    const d = await api('/api/experimental', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({operation:$('#labOp').value, text:$('#labText').value}) });
    $('#labOut').textContent = JSON.stringify(d, null, 2);
  } catch (e) { $('#labOut').textContent = e.message; }
});

(async () => {
  try { const h = await api('/health'); $('#health').textContent = `System ready · ${h.documents} document(s)`; }
  catch (e) { $('#health').textContent = 'System unavailable'; }
  try { await loadDocs(); await graph(); } catch (e) { status(e.message); }
})();
