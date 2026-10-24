import { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, BrainCircuit, CheckCircle2, ChevronRight, Lightbulb, PiggyBank, FileText, Sparkles, ArrowUpRight, Scale, Calculator, BarChart3 } from 'lucide-react';
import CitationPanel from '../components/CitationPanel';
import { Citation } from '../components/CitationBadge';
import { API_BASE_URL } from '../config/api';

const AnalysisDashboard = () => {
  const [data, setData] = useState<any>(null);
  const [aiExplanation, setAiExplanation] = useState<string>("Analyzing your profile and generating personalized advice...");
  const [explanationCitations, setExplanationCitations] = useState<Citation[]>([]);
  const [isAiLoading, setIsAiLoading] = useState<boolean>(true);
  const [profileName, setProfileName] = useState("");
  const [profile, setProfile] = useState<any>(null);
  
  // Chat state
  const [chatHistory, setChatHistory] = useState<{role: string, text: string, citations?: Citation[]}[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const savedResult = localStorage.getItem('analysisResult');
    const savedProfile = localStorage.getItem('taxProfile');
    
    if (savedResult && savedProfile) {
      const parsedResult = JSON.parse(savedResult);
      const parsedProfile = JSON.parse(savedProfile);
      setData(parsedResult);
      setProfile(parsedProfile);
      setProfileName(parsedProfile.name);
      
      // Fetch AI Explanation
      fetch(`${API_BASE_URL}/api/v1/ai/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: parsedProfile.name,
          recommendations: parsedResult.recommendations,
          total_benefit: parsedResult.total_potential_benefit
        })
      })
      .then(res => res.json())
      .then(aiData => {
        setAiExplanation(aiData.explanation);
        if (aiData.citations) setExplanationCitations(aiData.citations);
      })
      .catch(_err => {
        setAiExplanation("Unable to connect to AI Assistant. Please check backend logs.");
      })
      .finally(() => {
        setIsAiLoading(false);
      });
    }
  }, []);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory, isChatLoading, isAiLoading]);

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
          context: `User Profile: ${JSON.stringify(profile)}, Current Benefits: ${data?.total_potential_benefit}`
        }),
      });
      if (response.ok) {
        const resData = await response.json();
        setChatHistory(prev => [...prev, { role: 'ai', text: resData.reply, citations: resData.citations }]);
      }
    } catch (e) {
      setChatHistory(prev => [...prev, { role: 'ai', text: 'Sorry, I am having trouble connecting to the server.' }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-500 animate-fade-in">
        <FileText size={48} className="text-slate-300 mb-4" />
        <h2 className="text-xl font-bold text-slate-700 mb-2">No analysis found</h2>
        <p>Please submit your tax profile first.</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 animate-fade-in">
      <div className="mb-10">
        <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-2 tracking-tight">Tax Analysis Dashboard</h1>
        <p className="text-slate-600 font-medium">Hello {profileName}, here is your personalized tax report based on deterministic IT rules.</p>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 flex flex-col justify-between ring-1 ring-emerald-500/10">
          <div className="flex justify-between items-start mb-4">
            <div className="bg-emerald-50 p-3 rounded-2xl text-emerald-600">
              <PiggyBank size={24} strokeWidth={2.5} />
            </div>
          </div>
          <div>
            <p className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-1">Total Potential Benefit</p>
            <p className="text-2xl md:text-4xl font-extrabold text-emerald-600">₹{data.total_potential_benefit.toLocaleString()}</p>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 flex flex-col justify-between ring-1 ring-blue-500/10">
          <div className="flex justify-between items-start mb-4">
            <div className="bg-blue-50 p-3 rounded-2xl text-blue-600">
              <AlertCircle size={24} strokeWidth={2.5} />
            </div>
          </div>
          <div>
            <p className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-1">Unclaimed Deductions</p>
            <p className="text-2xl md:text-4xl font-extrabold text-slate-900">₹{data.total_unclaimed_deductions.toLocaleString()}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 flex flex-col justify-between ring-1 ring-amber-500/10">
          <div className="flex justify-between items-start mb-4">
            <div className="bg-amber-50 p-3 rounded-2xl text-amber-600">
              <Lightbulb size={24} strokeWidth={2.5} />
            </div>
          </div>
          <div>
            <p className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-1">High Priority Actions</p>
            <p className="text-2xl md:text-4xl font-extrabold text-slate-900">{data.high_priority_recommendation_count}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        
        {/* Left Column: Recommendations */}
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-2xl font-extrabold text-slate-900 flex items-center gap-2 mb-6">
            <CheckCircle2 className="text-emerald-500" size={28} />
            Tax Opportunities
          </h2>
          
          {data.recommendations.map((rec: any, idx: number) => (
            <div key={idx} className={`bg-white rounded-3xl shadow-sm border overflow-hidden hover:shadow-md transition-all group ${rec.is_planning ? 'border-amber-200 ring-1 ring-amber-500/10' : 'border-slate-200 hover:border-slate-300'}`}>
              <div className="p-6 md:p-8">
                <div className="flex flex-col md:flex-row md:justify-between md:items-start mb-6 gap-4">
                  <div>
                    <span className={`inline-block px-4 py-1.5 text-xs font-bold uppercase tracking-wider rounded-full mb-3 ${rec.is_planning ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-700'}`}>
                      {rec.is_planning ? 'Future Planning / Optimized' : rec.category}
                    </span>
                    <h3 className="text-xl font-bold text-slate-900 leading-snug">{rec.scheme_name}</h3>
                  </div>
                  <div className="md:text-right bg-emerald-50 md:bg-transparent p-3 md:p-0 rounded-xl">
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Tax Benefit</p>
                    <p className="text-2xl font-extrabold text-emerald-600">+₹{rec.potential_tax_benefit.toLocaleString()}</p>
                  </div>
                </div>
                
                {/* Rule Transparency Section */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 bg-slate-50 p-4 rounded-2xl border border-slate-100">
                  <div>
                    <div className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1 mb-1"><Scale size={12}/> Max Limit</div>
                    <div className="font-semibold text-slate-900">₹{rec.threshold_used.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1 mb-1"><CheckCircle2 size={12}/> Claimed</div>
                    <div className="font-semibold text-slate-900">₹{rec.current_investment.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1 mb-1"><BarChart3 size={12}/> Remaining</div>
                    <div className="font-semibold text-blue-600">₹{rec.gap_amount.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1 mb-1"><Calculator size={12}/> Trigger</div>
                    <div className="font-semibold text-slate-700 truncate text-sm" title={rec.triggered_rule}>{rec.triggered_rule}</div>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-5 mb-6 border border-indigo-100/50 relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-4 opacity-10">
                    <BrainCircuit size={64} />
                  </div>
                  <div className="flex items-center gap-2 mb-2 relative z-10">
                    <Sparkles size={16} className="text-indigo-600" />
                    <span className="text-xs font-extrabold text-indigo-700 uppercase tracking-widest">AI Explanation</span>
                  </div>
                  <p className="text-sm font-medium text-indigo-950/80 leading-relaxed relative z-10">{rec.explanation}</p>
                </div>

                <div className="flex flex-col md:flex-row md:items-center justify-between text-sm gap-4 pt-4 border-t border-slate-100">
                  <span className="text-slate-500 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                    <span className="font-medium">{rec.recommendation}</span>
                  </span>
                  <Link to="/rag-search" className="text-indigo-600 font-bold flex items-center gap-1 hover:text-indigo-800 transition-colors group/btn shrink-0">
                    Verify in Act: {rec.references[0]?.split('-')[1] || rec.references[0]} 
                    <ChevronRight size={16} className="group-hover/btn:translate-x-0.5 transition-transform" />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Right Column: AI Assistant & Citations */}
        <div className="lg:col-span-1">
          <div className="sticky top-24 bg-slate-900 rounded-3xl shadow-xl border border-slate-800 overflow-hidden flex flex-col h-[650px]">
            <div className="p-6 border-b border-white/10 bg-slate-900/50 backdrop-blur-md">
              <div className="flex items-center gap-4 text-white">
                <div className="bg-gradient-to-br from-violet-500 to-indigo-600 p-3 rounded-2xl shadow-inner">
                  <BrainCircuit size={24} className="text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-lg tracking-tight">TaxEase</h3>
                  <p className="text-xs text-slate-400 font-medium">AI-powered strategist</p>
                </div>
              </div>
            </div>
            
            <div ref={chatContainerRef} className="flex-1 p-6 overflow-y-auto space-y-6 bg-slate-950/50">
              
              {/* Initial AI Explanation */}
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0 mt-1">
                  <Sparkles size={14} className="text-white" />
                </div>
                <div className="bg-slate-800 rounded-2xl rounded-tl-none p-4 border border-slate-700/50 shadow-sm">
                  {isAiLoading ? (
                    <div className="flex items-center gap-2 text-slate-400 text-sm font-medium">
                      <div className="w-4 h-4 rounded-full border-2 border-slate-500 border-t-transparent animate-spin"></div>
                      Consulting with the AI...
                    </div>
                  ) : (
                    <div>
                      <div className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-medium">
                        {aiExplanation}
                      </div>
                      {explanationCitations.length > 0 && (
                        <CitationPanel citations={explanationCitations} />
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Chat History */}
              {chatHistory.map((msg, idx) => (
                <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 ${msg.role === 'user' ? 'bg-slate-700' : 'bg-indigo-600'}`}>
                    {msg.role === 'user' ? <span className="text-white text-xs font-bold">{profileName.charAt(0)}</span> : <Sparkles size={14} className="text-white" />}
                  </div>
                  <div className={`max-w-[85%] p-4 rounded-2xl shadow-sm ${msg.role === 'user' ? 'bg-slate-700 text-white rounded-tr-none border border-slate-600' : 'bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700/50'}`}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap font-medium">{msg.text}</p>
                    {msg.role === 'ai' && msg.citations && msg.citations.length > 0 && (
                      <CitationPanel citations={msg.citations} />
                    )}
                  </div>
                </div>
              ))}

              {isChatLoading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0 mt-1">
                    <Sparkles size={14} className="text-white" />
                  </div>
                  <div className="bg-slate-800 rounded-2xl rounded-tl-none p-4 border border-slate-700/50 shadow-sm flex items-center gap-2">
                     <div className="w-4 h-4 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></div>
                     <span className="text-slate-400 text-sm font-medium">Thinking...</span>
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-white/10 bg-slate-900">
              <div className="relative group">
                <input 
                  type="text" 
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleChat()}
                  placeholder="Ask a follow-up question..." 
                  disabled={isChatLoading || isAiLoading}
                  className="w-full bg-slate-800/50 border border-slate-700 rounded-xl py-4 pl-5 pr-14 text-slate-200 text-sm font-medium focus:outline-none focus:border-indigo-500 focus:bg-slate-800 transition-all disabled:opacity-50"
                />
                <button 
                  onClick={handleChat}
                  disabled={isChatLoading || isAiLoading || !chatInput.trim()}
                  className="absolute right-2 top-2 bottom-2 aspect-square bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 flex items-center justify-center transition-colors disabled:opacity-50"
                >
                  <ArrowUpRight size={18} strokeWidth={2.5} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisDashboard;
