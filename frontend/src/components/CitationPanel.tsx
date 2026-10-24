import React from 'react';
import { BookMarked } from 'lucide-react';
import CitationBadge, { Citation } from './CitationBadge';

interface CitationPanelProps {
  citations?: Citation[] | null;
  title?: string;
  className?: string;
}

export const CitationPanel: React.FC<CitationPanelProps> = ({
  citations,
  title = "Legal References (Income Tax Act, 1961)",
  className = ""
}) => {
  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className={`mt-3 pt-3 border-t border-slate-200/60 dark:border-slate-700/60 ${className}`}>
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">
        <BookMarked size={14} className="text-indigo-500" />
        <span>{title}</span>
        <span className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-1.5 py-0.5 rounded-full font-mono">
          {citations.length}
        </span>
      </div>
      <div className="flex flex-wrap items-center">
        {citations.map((citation, index) => (
          <CitationBadge key={`${citation.section_number}-${citation.page_number}-${index}`} citation={citation} />
        ))}
      </div>
    </div>
  );
};

export default CitationPanel;
