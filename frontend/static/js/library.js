/* Library page — copy-to-clipboard for the code samples.
   Mirrors the helper in train.js so the button works on this page too. */
window.copyCode = function (btn) {
  const code = btn.closest('.code-block').querySelector('code');
  if (!code) return;
  navigator.clipboard.writeText(code.textContent).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="bi bi-check-lg"></i> Copied!';
    setTimeout(() => { btn.innerHTML = orig; }, 2000);
  }).catch(() => {
    if (window.AMR && AMR.toast) {
      AMR.toast('Could not copy to clipboard', 'warning');
    }
  });
};
