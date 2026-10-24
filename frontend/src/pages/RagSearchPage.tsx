import { useState, useEffect } from 'react';
import { Search, Layers, ShieldCheck, Clock, AlertCircle, Sparkles, Loader2, ShieldAlert, ArrowDownRight, GitFork } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

interface ChunkResult {
  id?: number;
  text: string;
  metadata: {
    section_number?: string | null;
    chapter?: string | null;
    chapter_title?: string | null;
    subsection?: string | null;
    page_number: number;
    source_document: string;
    chunk_index: number;
  };
  score: number;
  raw_score?: number;
  dcavi_status?: string;
  applied_penalty?: number;
  conflict_reason?: string;
}

interface RagStatus {
  collection_name: string;
  points_count: number;
  vector_dimension: number;
  status: string;
  rag_enabled: boolean;
}

const RagSearchPage = () => {
  const [query, setQuery] = useState('');
  const [sectionFilter, setSectionFilter] = useState('');
  const [topK, setTopK] = useState(5);
  const [useDcavi, setUseDcavi] = useState(true);
  const [results, setResults] = useState<ChunkResult[]>([]);
  const [suppressed, setSuppressed] = useState<ChunkResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [retrievalTime, setRetrievalTime] = useState<number | null>(null);
  const [status, setStatus] = useState<RagStatus | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [showSuppressed, setShowSuppressed] = useState(true);

  useEffect(() => {
    // Fetch Qdrant collection status
    fetch(`${API_BASE_URL}/api/v1/rag/status`)
      .then(res => res.json())
      .then(data => setStatus(data))
      .catch(err => console.error("Failed to fetch RAG status:", err));
  }, []);

  const handleSearch = async (searchQuery?: string) => {
    const q = searchQuery !== undefined ? searchQuery : query;
    if (!q.trim()) return;

    setIsLoading(true);
    setHasSearched(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/rag/retrieve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: q,
          top_k: Number(topK),
          section_filter: sectionFilter.trim() || null,
          use_dcavi: useDcavi,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setResults(data.chunks || []);
        setSuppressed(data.suppressed_chunks || []);
        setRetrievalTime(data.retrieval_time_ms);
      } else {
        setResults([]);
        setSuppressed([]);
      }
    } catch (e) {
      console.error(e);
      setResults([]);
      setSuppressed([]);
    } finally {
      setIsLoading(false);
    }
  };

  const sampleQueries = [
    { label: "ULIP Contradiction (DCAVI Test)", q: "Is premium on unit linked insurance policy ULIP eligible for deduction under Section 80C?" },
    { label: "Standard Deduction (Amended)", q: "What is the standard deduction allowed from salaries under Section 16?" },
    { label: "Section 80D Health Insurance", q: "Health insurance deduction for senior citizen parents Section 80D" },
    { label: "NPS 80CCD(1B)", q: "Additional NPS deduction under Section 80CCD(1B)" }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100 mb-3">
          <Sparkles size={14} className="text-indigo-600" />
          <span>Dynamic Contradiction-Aware Vector Indexing (DCAVI)</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight mb-2">
          Income Tax Act, 1961 Search
        </h1>
        <p className="text-slate-600 font-medium">
          DCAVI-enhanced retrieval across 4,082 verified legislative chunks. Contradictory passages are mathematically suppressed using NLI conflict edges.
        </p>
      </div>

      {/* System Status Banner */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <ShieldCheck size={20} />
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Vector Store</p>
            <p className="text-sm font-bold text-slate-800">
              {status?.status === 'green' ? 'Online (Qdrant)' : status?.status || 'Connecting...'}
            </p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Layers size={20} />
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Indexed Chunks</p>
            <p className="text-sm font-bold text-slate-800">
              {status?.points_count ? status.points_count.toLocaleString() : '4,082'} Chunks
            </p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <GitFork size={20} />
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">DCAVI Engine</p>
            <p className="text-sm font-bold text-emerald-600">Active (P_con Gate)</p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center">
            <Clock size={20} />
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Embedding Dim</p>
            <p className="text-sm font-bold text-slate-800">{status?.vector_dimension || 768} (Gemini)</p>
          </div>
        </div>
      </div>

      {/* Search Input Bar */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm mb-8">
        <div className="flex flex-col md:flex-row gap-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Ask any tax question or describe a scenario (e.g. 'Is ULIP premium deductible under 80C?')..."
              className="w-full pl-12 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:border-indigo-500 focus:bg-white focus:ring-4 focus:ring-indigo-500/10 font-medium text-slate-800"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <input
              type="text"
              value={sectionFilter}
              onChange={(e) => setSectionFilter(e.target.value)}
              placeholder="Section filter (e.g. 80C)"
              className="w-40 px-4 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:border-indigo-500 focus:bg-white text-sm font-medium text-slate-800"
            />

            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="px-4 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:border-indigo-500 font-medium text-sm text-slate-700"
            >
              <option value={3}>Top 3</option>
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
            </select>

            {/* DCAVI Toggle */}
            <label className="flex items-center gap-2 px-3 py-3 bg-slate-50 border border-slate-200 rounded-2xl cursor-pointer select-none">
              <input
                type="checkbox"
                checked={useDcavi}
                onChange={(e) => setUseDcavi(e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500 h-4 w-4"
              />
              <span className="text-xs font-bold text-slate-700">DCAVI P_con</span>
            </label>

            <button
              onClick={() => handleSearch()}
              disabled={isLoading || !query.trim()}
              className="px-6 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-2xl transition-all shadow-md shadow-indigo-600/20 disabled:opacity-50 flex items-center gap-2"
            >
              {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
              Search Act
            </button>
          </div>
        </div>

        {/* Quick Sample Queries */}
        <div className="flex flex-wrap items-center gap-2 pt-2">
          <span className="text-xs font-semibold text-slate-400">Try testing:</span>
          {sampleQueries.map((item, i) => (
            <button
              key={i}
              onClick={() => {
                setQuery(item.q);
                handleSearch(item.q);
              }}
              className="text-xs px-3 py-1 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-600 rounded-lg transition-colors font-medium flex items-center gap-1"
            >
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* DCAVI Conflict Suppression Alert */}
      {suppressed.length > 0 && (
        <div className="mb-6 bg-amber-50 border border-amber-200 rounded-3xl p-6 shadow-xs animate-fade-in">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-700 flex items-center justify-center">
                <ShieldAlert size={20} />
              </div>
              <div>
                <h3 className="font-bold text-amber-900 text-base">
                  DCAVI Intercepted & Suppressed {suppressed.length} Contradictory Passage(s)
                </h3>
                <p className="text-xs text-amber-700 font-medium">
                  Dynamic contradiction penalty P_con was applied to expel superseded/stale assertions (Theorem 1).
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowSuppressed(!showSuppressed)}
              className="text-xs font-bold text-amber-800 hover:text-amber-950 underline cursor-pointer"
            >
              {showSuppressed ? 'Hide Suppressed Passages' : 'View Suppressed Passages'}
            </button>
          </div>

          {showSuppressed && (
            <div className="mt-4 space-y-3 pt-3 border-t border-amber-200/60">
              {suppressed.map((chunk, idx) => (
                <div key={idx} className="bg-white/80 p-4 rounded-2xl border border-amber-200 text-xs">
                  <div className="flex items-center justify-between mb-2 pb-2 border-b border-amber-100">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-red-100 text-red-700 font-bold rounded">
                        SUPPRESSED (Chunk #{chunk.id})
                      </span>
                      <span className="font-semibold text-slate-600">
                        Section {chunk.metadata.section_number || 'N/A'} · Page {chunk.metadata.page_number}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-500 font-mono text-[11px]">
                      <span>Raw Cosine: {(chunk.raw_score || chunk.score).toFixed(3)}</span>
                      <ArrowDownRight size={14} className="text-red-500" />
                      <span className="text-red-600 font-bold">DCAVI Score: {chunk.score.toFixed(1)}</span>
                    </div>
                  </div>
                  {chunk.conflict_reason && (
                    <p className="text-amber-900 font-semibold mb-2">
                      Reason: {chunk.conflict_reason}
                    </p>
                  )}
                  <p className="text-slate-600 line-clamp-2 italic font-serif">
                    "{chunk.text}"
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Results Header */}
      {hasSearched && (
        <div className="flex items-center justify-between mb-4 px-1">
          <p className="text-sm font-bold text-slate-600">
            Retrieved {results.length} Authoritative Legislative Chunks {useDcavi && '(DCAVI Verified)'}
          </p>
          {retrievalTime !== null && (
            <p className="text-xs font-mono text-slate-400">
              Retrieved in {retrievalTime} ms
            </p>
          )}
        </div>
      )}

      {/* Results List */}
      <div className="space-y-4">
        {results.map((chunk, index) => {
          const scorePercent = Math.round((chunk.raw_score || chunk.score) * 100);
          const isVerified = chunk.dcavi_status === 'VERIFIED';
          return (
            <div
              key={chunk.id || index}
              className={`bg-white rounded-3xl p-6 border shadow-xs hover:shadow-md transition-all ${
                isVerified ? 'border-emerald-300 ring-1 ring-emerald-500/15' : 'border-slate-200 hover:border-indigo-300'
              }`}
            >
              {/* Header Badges */}
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-100">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-3 py-1 bg-indigo-600 text-white font-bold text-xs rounded-lg shadow-2xs">
                    {chunk.metadata.section_number ? `Section ${chunk.metadata.section_number}` : 'Statutory Text'}
                  </span>
                  {chunk.metadata.chapter && (
                    <span className="px-3 py-1 bg-slate-100 text-slate-700 font-semibold text-xs rounded-lg">
                      Chapter {chunk.metadata.chapter}
                    </span>
                  )}
                  <span className="px-3 py-1 bg-blue-50 text-blue-700 font-semibold text-xs rounded-lg">
                    Page {chunk.metadata.page_number}
                  </span>
                  {isVerified && (
                    <span className="px-2.5 py-1 bg-emerald-100 text-emerald-800 font-bold text-xs rounded-lg flex items-center gap-1">
                      <ShieldCheck size={13} />
                      DCAVI Authoritative Winner
                    </span>
                  )}
                </div>

                {/* Score pill */}
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-500">Cosine Match:</span>
                  <div className="w-20 bg-slate-100 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-indigo-600 h-2.5 rounded-full"
                      style={{ width: `${Math.min(100, Math.max(0, scorePercent))}%` }}
                    />
                  </div>
                  <span className="text-xs font-bold font-mono text-indigo-700">
                    {(chunk.raw_score || chunk.score).toFixed(3)}
                  </span>
                </div>
              </div>

              {/* Conflict resolution note if verified */}
              {chunk.conflict_reason && (
                <div className="mb-3 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 font-medium">
                  <span className="font-bold">DCAVI Precedence: </span>
                  {chunk.conflict_reason}
                </div>
              )}

              {/* Chapter Title */}
              {chunk.metadata.chapter_title && (
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  {chunk.metadata.chapter_title}
                </p>
              )}

              {/* Chunk text */}
              <p className="text-slate-800 text-sm leading-relaxed whitespace-pre-wrap font-serif bg-slate-50/70 p-4 rounded-2xl border border-slate-100">
                {chunk.text}
              </p>

              {/* Footer source note */}
              <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
                <span>Source: {chunk.metadata.source_document} · Chunk #{chunk.id || chunk.metadata.chunk_index}</span>
                <span className="text-indigo-600 font-semibold">Income Tax Department, Govt of India</span>
              </div>
            </div>
          );
        })}

        {hasSearched && results.length === 0 && !isLoading && (
          <div className="text-center py-12 bg-white rounded-3xl border border-slate-200">
            <AlertCircle size={40} className="mx-auto text-slate-300 mb-3" />
            <p className="font-bold text-slate-700 text-base">No statutory chunks matched your query</p>
            <p className="text-sm text-slate-400 mt-1">Try lowering the section filter or using broader tax terms.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default RagSearchPage;
