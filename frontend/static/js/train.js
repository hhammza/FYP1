/* ============================================================
   AMRPredict — Train Page (train.html)
   Reload models via fetch and copy code-block to clipboard.
   Expects: window.AMR (from main.js)
   ============================================================ */

window.reloadModels = function (btn) {
  btn = btn || event.currentTarget;
  const orig = btn.innerHTML;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Reloading…';
  btn.disabled = true;

  fetch('/reload', { method: 'POST' })
    .then(r => r.json())
    .then(data => {
      const trained = Object.entries(data.models || {})
        .map(([k, v]) => `${k}: ${v.trained ? '✅ Trained' : '⚠️ Heuristic'}`)
        .join(' &nbsp;|&nbsp; ');
      const div = document.getElementById('reloadResult');
      if (div) {
        div.innerHTML = `<div class="alert alert-success-custom"><i class="bi bi-check-circle me-2"></i>${trained}</div>`;
      }
      AMR.toast('Models reloaded successfully', 'success', 'Reload Complete');
    })
    .catch(e => {
      const div = document.getElementById('reloadResult');
      if (div) {
        div.innerHTML = `<div class="alert alert-danger-custom"><i class="bi bi-exclamation-circle me-2"></i>${e.message}</div>`;
      }
      AMR.toast(e.message, 'error', 'Reload Failed');
    })
    .finally(() => {
      btn.innerHTML = orig;
      btn.disabled = false;
    });
};

window.copyCode = function (btn) {
  const code = btn.closest('.code-block').querySelector('code');
  if (!code) return;
  navigator.clipboard.writeText(code.textContent).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="bi bi-check-lg"></i> Copied!';
    setTimeout(() => { btn.innerHTML = orig; }, 2000);
  }).catch(() => {
    AMR.toast('Could not copy to clipboard', 'warning');
  });
};
