import { useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router';
import Navbar from './Navbar';
import Footer from './Footer';
import { useHealth } from '../lib/health';
import { usePageEffects } from '../lib/pageEffects';

export default function Layout() {
  const { pathname } = useLocation();
  const { health } = useHealth();
  const [main, setMain] = useState<HTMLElement | null>(null);

  // A new page opens at the top, as a full page load did
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  usePageEffects(main, [pathname, health]);

  return (
    <>
      <Navbar />
      <main className="main-content" ref={setMain}>
        <Outlet />
      </main>
      <Footer />
    </>
  );
}
