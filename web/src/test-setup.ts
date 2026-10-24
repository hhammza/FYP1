import '@testing-library/jest-dom/vitest';

// jsdom has no layout, so no scrolling
window.scrollTo = (() => {}) as typeof window.scrollTo;
