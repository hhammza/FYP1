import { Route, Routes } from 'react-router';
import Layout from './components/Layout';
import About from './pages/About';
import Datasets from './pages/Datasets';
import Forecast from './pages/Forecast';
import Home from './pages/Home';
import Library from './pages/Library';
import NotFound from './pages/NotFound';
import NotYet from './pages/NotYet';
import Predict from './pages/Predict';
import Timeline from './pages/Timeline';

/* Pages still served by the Flask site until each one is moved over. */
const PENDING: [string, string][] = [
  ['/models', 'Model Report'],
  ['/compare', 'Deployed vs Experimental'],
  ['/genes', 'Resistance Genes'],
  ['/train', 'Train Models'],
];

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/datasets" element={<Datasets />} />
        <Route path="/forecast" element={<Forecast />} />
        <Route path="/predict" element={<Predict />} />
        <Route path="/predict/sample" element={<Predict sample />} />
        <Route path="/timeline" element={<Timeline />} />
        <Route path="/timeline/sample" element={<Timeline sample />} />
        <Route path="/library" element={<Library />} />
        {PENDING.map(([path, title]) => <Route key={path} path={path} element={<NotYet title={title} />} />)}
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
