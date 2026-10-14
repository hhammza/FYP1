/* The small animations every page shares (initNumberAnimation, initProbBars,
   initTooltips and initAlertAutoDismiss in the old main.js), run over the
   page's DOM each time a page opens or its data arrives. */
import { useEffect } from 'react';
import { Tooltip } from 'bootstrap';

/* Numbers being counted up right now: a second run of the effects (a result
   arriving, say) must not start again from the half-counted text */
const counting = new WeakSet<Element>();

function animateCount(el: HTMLElement, end: number, originalText: string, duration: number) {
  counting.add(el);
  /* "$100T" -> prefix "$", number "100", suffix "T"; the frame text keeps that shape */
  const m = originalText.match(/^(\D*?)([\d.,]+)(.*)$/) || ['', '', originalText, ''];
  const prefix = m[1], suffix = m[3];
  const isFloat = m[2].includes('.');
  const decimals = isFloat ? (m[2].split('.')[1] || '').replace(/[^0-9]/g, '').length : 0;
  const startTime = performance.now();
  function update(now: number) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = end * eased;
    el.textContent = prefix + (isFloat ? current.toFixed(decimals) : Math.round(current).toLocaleString()) + suffix;
    if (progress < 1) requestAnimationFrame(update);
    else {
      el.textContent = originalText;
      el.dataset.counted = originalText;
      counting.delete(el);
    }
  }
  requestAnimationFrame(update);
}

/** Runs the effects inside `root` whenever one of `deps` changes. */
export function usePageEffects(root: HTMLElement | null, deps: unknown[]) {
  useEffect(() => {
    if (!root) return;
    const cleanups: (() => void)[] = [];
    const hasIO = typeof IntersectionObserver !== 'undefined';

    if (hasIO) {
      const counter = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          const el = entry.target as HTMLElement;
          counter.unobserve(el);
          const text = el.dataset.target || el.textContent || '';
          // once per value, as a page load did: not again when another part of the page changes
          if (counting.has(el) || el.dataset.counted === text) return;
          const num = parseFloat(text.replace(/[^0-9.]/g, ''));
          if (!isNaN(num) && num > 0 && text.length < 10) animateCount(el, num, text, 900);
        });
      }, { threshold: 0.3 });
      /* .stat-mini-static opts out: values like "9 vs 37" are not one number */
      root.querySelectorAll('.stat-mini-value:not(.stat-mini-static), .stat-number, .hpanel-stat-val')
        .forEach(el => counter.observe(el));
      cleanups.push(() => counter.disconnect());

      const bars = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          entry.target.querySelectorAll<HTMLElement>('.prob-bar-fill, .hpanel-bar-fill, .kmer-bar, .gene-fill')
            .forEach(bar => {
              const target = bar.style.width;
              bar.style.width = '0';
              requestAnimationFrame(() => {
                bar.style.transition = 'width 0.9s cubic-bezier(0.4,0,0.2,1)';
                bar.style.width = target;
              });
            });
          bars.unobserve(entry.target);
        });
      }, { threshold: 0.2 });
      root.querySelectorAll('.result-hero, .info-card, .gene-row, .hpanel-bars').forEach(el => bars.observe(el));
      cleanups.push(() => bars.disconnect());
    }

    const tips = Array.from(root.querySelectorAll('[data-bs-toggle="tooltip"]'))
      .map(el => new Tooltip(el, { trigger: 'hover focus' }));
    cleanups.push(() => tips.forEach(t => t.dispose()));

    const timers = Array.from(root.querySelectorAll<HTMLElement>('.alert-success-custom')).map(alert =>
      setTimeout(() => {
        alert.style.transition = 'opacity 0.5s';
        alert.style.opacity = '0';
        setTimeout(() => { alert.style.display = 'none'; }, 500);
      }, 7000));
    cleanups.push(() => timers.forEach(clearTimeout));

    return () => cleanups.forEach(f => f());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [root, ...deps]);
}

/** Sets the browser tab's title, as the templates' {% block title %} did. */
export function useTitle(title: string) {
  useEffect(() => { document.title = `${title} | BioAnalytics FYP`; }, [title]);
}
