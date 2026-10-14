/* Light/dark theme, remembered per browser; charts re-colour on a change. */
import { useEffect, useState } from 'react';

export const THEME_EVENT = 'amr-theme';

export const isDark = (): boolean => document.documentElement.getAttribute('data-theme') === 'dark';

export function setTheme(dark: boolean) {
  if (dark) document.documentElement.setAttribute('data-theme', 'dark');
  else document.documentElement.removeAttribute('data-theme');
  try { localStorage.setItem('amr-theme', dark ? 'dark' : 'light'); } catch { /* storage blocked */ }
  window.dispatchEvent(new Event(THEME_EVENT));
}

/** true while the dark theme is on; re-renders the caller on a change. */
export function useDarkTheme(): boolean {
  const [dark, setDark] = useState(isDark);
  useEffect(() => {
    const update = () => setDark(isDark());
    window.addEventListener(THEME_EVENT, update);
    return () => window.removeEventListener(THEME_EVENT, update);
  }, []);
  return dark;
}

/** Plotly layout colours for the current theme (AMR.plotLayout in the old main.js). */
export function plotTheme() {
  const dark = isDark();
  return {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    tickColor: dark ? '#94a3b8' : '#64748b',
    gridColor: dark ? 'rgba(255,255,255,0.06)' : 'rgba(15,23,42,0.08)',
    lineColor: dark ? 'rgba(255,255,255,0.10)' : 'rgba(15,23,42,0.12)',
    fontFamily: "'Inter',-apple-system,sans-serif",
  };
}
