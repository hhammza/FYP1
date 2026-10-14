import { Route, Routes } from 'react-router';
import Layout from './components/Layout';
import About from './pages/About';
import Compare from './pages/Compare';
import Datasets from './pages/Datasets';
import Forecast from './pages/Forecast';
import Genes from './pages/Genes';
import Home from './pages/Home';
import Library from './pages/Library';
import Models from './pages/Models';
import NotFound from './pages/NotFound';
import Predict from './pages/Predict';
import Timeline from './pages/Timeline';
import Train from './pages/Train';

/* Every page of the Flask site (frontend/app.py), in the order of its navbar. */
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="/forecast" element={<Forecast />} />
        <Route path="/predict" element={<Predict />} />
        <Route path="/predict/sample" element={<Predict sample />} />
        <Route path="/timeline" element={<Timeline />} />
        <Route path="/timeline/sample" element={<Timeline sample />} />
        <Route path="/models" element={<Models />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/datasets" element={<Datasets />} />
        <Route path="/genes" element={<Genes />} />
        <Route path="/library" element={<Library />} />
        <Route path="/about" element={<About />} />
        <Route path="/train" element={<Train />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
