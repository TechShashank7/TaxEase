import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import TaxProfilePage from './pages/TaxProfilePage';
import AnalysisDashboard from './pages/AnalysisDashboard';
import AIAssistantPage from './pages/AIAssistantPage';
import RagSearchPage from './pages/RagSearchPage';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/profile" element={<TaxProfilePage />} />
          <Route path="/dashboard" element={<AnalysisDashboard />} />
          <Route path="/assistant" element={<AIAssistantPage />} />
          <Route path="/rag-search" element={<RagSearchPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
