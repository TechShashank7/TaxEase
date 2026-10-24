import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, ShieldCheck } from 'lucide-react';

export interface Citation {
  section_number?: string | null;
  chapter?: string | null;
  chapter_title?: string | null;
  page_number: number;
  source_document?: string;
  excerpt: string;
  relevance_score?: number;
  dcavi_status?: string;
  conflict_reason?: string;
}

interface CitationBadgeProps {
  citation: Citation;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ citation }) => {
  const [isOpen, setIsOpen] = useState(false);

  const sectionLabel = citation.section_number
    ? `Section ${citation.section_number}`
    : 'Income Tax Act';
  const pageLabel = `Page ${citation.page_number}`;
  const chapterLabel = citation.chapter ? `Ch. ${citation.chapter}` : null;
  const scorePercent = citation.relevance_score
    ? Math.round(citation.relevance_score * 100)
    : null;

  return (
    <div className="inline-block my-1 mr-2 text-left">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200/80 transition-colors shadow-2xs group"
        title="Click to view official Act excerpt"
      >
        <BookOpen size={12} className="text-indigo-500 group-hover:text-indigo-700" />
        <span className="font-bold">{sectionLabel}</span>
        {chapterLabel && <span className="text-indigo-400 font-normal">· {chapterLabel}</span>}
        <span className="text-indigo-500 font-normal">· {pageLabel}</span>
        {scorePercent && (
          <span className="bg-indigo-200/60 text-indigo-800 text-[10px] font-mono px-1.5 py-0.2 rounded-full">
            {scorePercent}%
          </span>
        )}
        {citation.dcavi_status === 'VERIFIED' && (
          <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-1.5 py-0.2 rounded-full flex items-center gap-0.5">
            DCAVI ✓
          </span>
        )}
        {isOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {isOpen && (
        <div className="mt-1.5 p-3.5 bg-slate-900 text-slate-100 rounded-xl text-xs shadow-xl border border-slate-800 max-w-md animate-fade-in z-20 relative">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-slate-400">
            <div className="flex items-center gap-1.5 text-indigo-400 font-semibold">
              <ShieldCheck size={14} className="text-emerald-400" />
              <span>{citation.source_document || 'Income Tax Act, 1961'}</span>
            </div>
            <span className="text-[11px] font-mono text-slate-400">Page {citation.page_number}</span>
          </div>
          {citation.chapter_title && (
            <p className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold mb-1">
              {citation.chapter_title}
            </p>
          )}
          <p className="text-slate-300 italic leading-relaxed bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
            "{citation.excerpt}"
          </p>
          {citation.conflict_reason && (
            <div className="mt-2 text-[10px] bg-emerald-950/70 border border-emerald-800/60 p-2 rounded-md text-emerald-300">
              <span className="font-bold">DCAVI Authority Resolution: </span>
              {citation.conflict_reason}
            </div>
          )}
          <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400 pt-1">
            <span>Cosine Relevance: {(citation.relevance_score || 0).toFixed(3)}</span>
            <span className="text-emerald-400 font-medium">
              {citation.dcavi_status ? `DCAVI: ${citation.dcavi_status}` : 'Verified by TaxEase RAG'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default CitationBadge;
