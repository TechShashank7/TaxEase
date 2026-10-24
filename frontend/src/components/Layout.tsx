import React from 'react';
import Navbar from './Navbar';
import { Sparkles } from 'lucide-react';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col bg-white font-sans selection:bg-blue-100 selection:text-blue-900">
      <Navbar />

      {/* Disclaimer Banner */}
      <div className="bg-amber-50 text-amber-900 border-b border-amber-200/80">
        <div className="max-w-7xl mx-auto px-4 py-2 text-xs font-medium text-center">
          <span className="font-semibold uppercase tracking-wider text-amber-700 mr-1.5">Disclaimer</span>
          TaxEase provides AI-assisted guidance based on the Income Tax Act rules. It is not a substitute for a certified Chartered Accountant.
        </div>
      </div>

      <main className="flex-grow flex flex-col">
        {children}
      </main>

      <footer className="bg-slate-950 border-t border-slate-800 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex flex-col md:flex-row justify-between items-start gap-8">
            {/* Brand */}
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                  <Sparkles size={14} className="text-white" />
                </div>
                <span className="font-bold text-white text-base tracking-tight">
                  TaxEase<span className="text-blue-400">AI</span>
                </span>
              </div>
              <p className="text-sm text-slate-400 max-w-xs leading-relaxed">
                Intelligent tax optimization for Indian taxpayers. Powered by Income Tax Act rules and AI reasoning.
              </p>
            </div>

            {/* Links */}
            <div className="flex flex-col gap-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Legal</p>
              <span className="text-sm text-slate-400 hover:text-slate-200 cursor-pointer transition-colors">Privacy Policy</span>
              <span className="text-sm text-slate-400 hover:text-slate-200 cursor-pointer transition-colors">Terms of Service</span>
              <span className="text-sm text-slate-400 hover:text-slate-200 cursor-pointer transition-colors">Disclaimer</span>
            </div>
          </div>

          <div className="border-t border-slate-800 mt-10 pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-slate-500">
              &copy; {new Date().getFullYear()} TaxEaseAI. All rights reserved.
            </p>
            <p className="text-xs text-slate-600">
              Not a substitute for professional tax advice. Consult a CA for binding decisions.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
