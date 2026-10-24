import { useState, useEffect } from 'react';
import { BrainCircuit, SlidersHorizontal, Calculator, ArrowUpRight, Loader2, Sparkles } from 'lucide-react';
import CitationPanel from '../components/CitationPanel';
import { Citation } from '../components/CitationBadge';
import { API_BASE_URL } from '../config/api';

const AIAssistantPage = () => {
  const [profile, setProfile] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Simulator state
  const [simRegime, setSimRegime] = useState('old');
  const [simHomeLoan, setSimHomeLoan] = useState<number | ''>('');
  const [simSalaryBump, setSimSalaryBump] = useState<number | ''>('');

  const [chatHistory, setChatHistory] = useState<{role: string, text: string, citations?: Citation[]}[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);

  useEffect(() => {
    const p = localStorage.getItem('taxProfile');
    const r = localStorage.getItem('analysisResult');
    if (p) {
      const parsed = JSON.parse(p);
      setProfile(parsed);
      setSimRegime(parsed.tax_regime || 'old');
    }
    if (r) setResult(JSON.parse(r));
  }, []);

  const handleSimulate = async () => {
    if (!profile) return;
    setIsLoading(true);
    
    const modifiedProfile = {
      ...profile,
      tax_regime: simRegime,
      home_loan_interest: (profile.home_loan_interest || 0) + Number(simHomeLoan || 0),
      basic_salary: (profile.basic_salary || 0) + Number(simSalaryBump || 0),
      annual_income: (profile.annual_income || 0) + Number(simSalaryBump || 0)
    };

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/eligibility/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(modifiedProfile),
      });
      if (response.ok) {
        const newResult = await response.json();
        setResult(newResult);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChat = async () => {
    if (!chatInput.trim() || !profile) return;
    
    const userMessage = chatInput;
    setChatHistory(prev => [...prev, { role: 'user', text: userMessage }]);
    setChatInput("");
    setIsChatLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          context: `User Profile: ${JSON.stringify(profile)}, Current Benefits: ${result?.total_potential_benefit}`
        }),
      });
      if (response.ok) {
        const data = await response.json();
        setChatHistory(prev => [...prev, { role: 'ai', text: data.reply, citations: data.citations }]);
      }
    } catch (e) {
      setChatHistory(prev => [...prev, { role: 'ai', text: 'Sorry, I am having trouble connecting to the server.' }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  if (!profile || !result) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-500 animate-fade-in">
        <BrainCircuit size={48} className="text-slate-300 mb-4" />
        <h2 className="text-xl font-bold text-slate-700 mb-2">Profile Required</h2>
        <p>Please submit your tax profile first to use the simulator.</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight mb-2">Interactive AI & Simulator</h1>
        <p className="text-slate-600 font-medium">Chat with the AI about tax provisions or run What-If scenarios.</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8 h-[75vh]">
        
        {/* Chat Area */}
        <div className="flex-1 bg-white rounded-3xl shadow-sm border border-slate-200 flex flex-col overflow-hidden ring-1 ring-slate-900/5">
          <div className="p-6 border-b border-slate-100 bg-white flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-indigo-50 text-indigo-600 p-3 rounded-2xl">
                <BrainCircuit size={24} />
              </div>
              <div>
                <h2 className="font-bold text-slate-900 text-lg">AI Tax Expert</h2>
                <p className="text-xs font-medium text-slate-500">Ask any IT Act question</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs font-bold uppercase tracking-wider">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Online
            </div>
          </div>
          
          <div className="flex-1 p-8 overflow-y-auto bg-slate-50 flex flex-col gap-4">
            {chatHistory.length === 0 ? (
              <div className="text-center text-slate-400 text-sm m-auto">
                <Sparkles size={32} className="mx-auto mb-4 opacity-50 text-indigo-500" />
                <p className="font-medium text-slate-600 text-base">Hi {profile.name}! I'm ready to answer your tax questions.</p>
                <p className="mt-2">Try asking: "Why am I eligible for 80D?"</p>
              </div>
            ) : (
              chatHistory.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-4 rounded-2xl ${msg.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-white border border-slate-200 text-slate-700 rounded-tl-none shadow-sm'}`}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap font-medium">{msg.text}</p>
                    {msg.role === 'ai' && msg.citations && msg.citations.length > 0 && (
                      <CitationPanel citations={msg.citations} />
                    )}
                  </div>
                </div>
              ))
            )}
            {isChatLoading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] p-4 rounded-2xl bg-white border border-slate-200 text-slate-500 rounded-tl-none shadow-sm flex items-center gap-2">
                   <div className="w-4 h-4 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></div>
                   Thinking...
                </div>
              </div>
            )}
          </div>
          
          <div className="p-6 border-t border-slate-100 bg-white">
            <div className="relative group">
              <input 
                type="text" 
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleChat()}
                className="w-full px-5 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:border-indigo-500 focus:bg-white focus:ring-4 focus:ring-indigo-500/10 transition-all font-medium text-slate-700"
                placeholder="Ask a question..."
                disabled={isChatLoading}
              />
              <button onClick={handleChat} disabled={isChatLoading || !chatInput.trim()} className="absolute right-2 top-2 bottom-2 aspect-square bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 flex items-center justify-center transition-colors shadow-sm disabled:opacity-50">
                <ArrowUpRight size={20} strokeWidth={2.5} />
              </button>
            </div>
          </div>
        </div>

        {/* What-If Simulator */}
        <div className="w-full lg:w-96 bg-slate-900 rounded-3xl shadow-xl border border-slate-800 overflow-hidden flex flex-col">
          <div className="p-6 border-b border-white/10 bg-slate-900 flex items-center gap-4">
            <div className="bg-emerald-500/20 text-emerald-400 p-3 rounded-2xl">
              <SlidersHorizontal size={24} />
            </div>
            <div>
              <h2 className="font-bold text-white text-lg">Simulator</h2>
              <p className="text-xs font-medium text-slate-400">Rules Engine recalculation</p>
            </div>
          </div>
          
          <div className="p-6 flex-1 overflow-y-auto bg-slate-900">
            <p className="text-sm font-medium text-slate-400 mb-8 leading-relaxed">
              Tweak your financial profile and see how it impacts your deterministic tax benefits instantly.
            </p>
            
            <div className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/5 border border-emerald-500/20 p-5 rounded-2xl mb-8 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest mb-1 text-emerald-400">Simulated Benefit</p>
                <p className="text-3xl font-extrabold text-white">₹{result.total_potential_benefit.toLocaleString()}</p>
              </div>
              <div className="text-emerald-500/50">
                <Calculator size={32} />
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Switch Regime</label>
                <select 
                  value={simRegime}
                  onChange={(e) => setSimRegime(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-700 rounded-xl bg-slate-800 text-white font-medium focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none appearance-none"
                >
                  <option value="old">Old Tax Regime</option>
                  <option value="new">New Tax Regime</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Add Home Loan Interest (₹)</label>
                <input 
                  type="number" 
                  value={simHomeLoan}
                  onChange={(e) => setSimHomeLoan(e.target.value === '' ? '' : Number(e.target.value))}
                  placeholder="e.g. 200000"
                  className="w-full px-4 py-3 border border-slate-700 rounded-xl bg-slate-800 text-white font-medium focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none placeholder:text-slate-600" 
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Increase Salary By (₹)</label>
                <input 
                  type="number" 
                  value={simSalaryBump}
                  onChange={(e) => setSimSalaryBump(e.target.value === '' ? '' : Number(e.target.value))}
                  placeholder="e.g. 50000"
                  className="w-full px-4 py-3 border border-slate-700 rounded-xl bg-slate-800 text-white font-medium focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none placeholder:text-slate-600" 
                />
              </div>
              
              <button 
                onClick={handleSimulate}
                disabled={isLoading}
                className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold mt-4 transition-all disabled:opacity-70 flex justify-center items-center gap-2 shadow-lg shadow-indigo-600/20"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={20} className="animate-spin" />
                    Calculating...
                  </>
                ) : 'Run Simulation'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIAssistantPage;
