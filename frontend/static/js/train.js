/* ============================================================
   AMRPredict — Train Page (train.html)
   Reload models via fetch and copy code-block to clipboard. Both train
   forms and the reload button send the admin password (#adminToken).
   Expects: window.AMR (from main.js)
   ============================================================ */

function adminToken() {
  const el = document.getElementById('adminToken');
  return el ? el.value : '';
}

/* Copy the password into the train form being submitted; stop if empty */
document.querySelectorAll('form[action="/train"]').forEach(form => {
  form.addEventListener('submit', e => {
    const token = adminToken();
    if (!token) {
      e.preventDefault();
      AMR.toast('Enter the admin password first.', 'error', 'Password needed');
      document.getElementById('adminToken')?.focus();
      return;
    }
    form.querySelector('.admin-token-field').value = token;
  });
});

window.reloadModels = function (btn) {
  btn = btn || event.currentTarget;
  const orig = btn.innerHTML;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Reloading…';
  btn.disabled = true;

  fetch('/reload', { method: 'POST', headers: { 'X-Admin-Token': adminToken() } })
    .then(r => r.json().then(data => {
      if (!r.ok) throw new Error(data.error || `Reload failed (HTTP ${r.status})`);
      return data;
    }))
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
