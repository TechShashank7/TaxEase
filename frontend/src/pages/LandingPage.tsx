import { Link } from 'react-router-dom';
import {
  ArrowRight,
  BrainCircuit,
  FileSearch,
  PiggyBank,
  CheckCircle2,
  TrendingUp,
  ShieldCheck,
  Lightbulb,
  ChevronDown,
  Sparkles,
  BarChart3,
  Target,
  Users,
  Lock,
} from 'lucide-react';

// ─── Product Dashboard Mock ───────────────────────────────────────────────────

const DashboardPreview = () => (
  <div className="relative w-full max-w-md mx-auto animate-float">
    {/* Glow orb behind card */}
    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-indigo-500/20 rounded-3xl blur-3xl scale-110 pointer-events-none" />

    {/* Main card */}
    <div className="relative bg-white rounded-2xl shadow-card border border-slate-200/80 overflow-hidden">
      {/* Card header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-white/20 rounded-md flex items-center justify-center">
              <Sparkles size={12} className="text-white" />
            </div>
            <span className="text-white font-semibold text-sm">Tax Analysis Report</span>
          </div>
          <span className="text-blue-200 text-xs font-medium">FY 2025–26</span>
        </div>
      </div>

      <div className="p-5 space-y-4">
        {/* Savings Potential */}
        <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl p-4 border border-emerald-100">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600">Tax Savings Potential</span>
            <TrendingUp size={14} className="text-emerald-500" />
          </div>
          <div className="flex items-end gap-1.5">
            <span className="text-3xl font-extrabold text-slate-900 tracking-tight">₹42,500</span>
            <span className="text-emerald-600 text-sm font-semibold mb-0.5">/ year</span>
          </div>
          <div className="mt-2 h-1.5 bg-emerald-100 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full" style={{ width: '72%' }} />
          </div>
          <p className="text-xs text-emerald-700 mt-1">72% of maximum benefit utilized</p>
        </div>

        {/* Eligible Sections */}
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Eligible Sections</p>
            <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">4 Found</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {[
              { label: 'Section 80C', desc: 'Investments & LIC', amount: '₹1.5L' },
              { label: 'Section 80D', desc: 'Health Insurance', amount: '₹25K' },
              { label: 'HRA Exemption', desc: 'House Rent', amount: '₹96K' },
              { label: 'NPS (80CCD)', desc: 'Pension Scheme', amount: '₹50K' },
            ].map((s) => (
              <div key={s.label} className="flex items-start gap-2 bg-slate-50 rounded-lg p-2.5 border border-slate-100">
                <CheckCircle2 size={14} className="text-emerald-500 mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs font-semibold text-slate-800">{s.label}</p>
                  <p className="text-[10px] text-slate-400">{s.desc}</p>
                  <p className="text-[10px] font-bold text-emerald-600 mt-0.5">{s.amount}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Insight */}
        <div className="bg-gradient-to-r from-violet-50 to-indigo-50 rounded-xl p-3.5 border border-violet-100">
          <div className="flex gap-2.5">
            <div className="w-6 h-6 bg-violet-100 rounded-md flex items-center justify-center shrink-0 mt-0.5">
              <BrainCircuit size={12} className="text-violet-600" />
            </div>
            <div>
              <p className="text-xs font-bold text-violet-800 mb-1">AI Insight</p>
              <p className="text-xs text-violet-700 leading-relaxed">
                You may qualify for an additional <span className="font-bold">₹8,200</span> deduction under 80CCD(1B) by contributing to NPS Tier-1.
              </p>
            </div>
          </div>
        </div>

        {/* Optimization Score */}
        <div className="flex items-center justify-between pt-1">
          <span className="text-xs text-slate-500 font-medium">Optimization Score</span>
          <div className="flex items-center gap-2">
            <div className="flex gap-0.5">
              {[1,2,3,4,5].map((i) => (
                <div
                  key={i}
                  className={`h-2 w-5 rounded-sm ${i <= 4 ? 'bg-blue-500' : 'bg-slate-200'}`}
                />
              ))}
            </div>
            <span className="text-xs font-bold text-slate-700">4/5</span>
          </div>
        </div>
      </div>
    </div>

    {/* Floating badges */}
    <div className="absolute -bottom-4 -left-4 bg-white rounded-xl shadow-card border border-slate-200 px-3 py-2 flex items-center gap-2">
      <div className="w-6 h-6 bg-emerald-100 rounded-lg flex items-center justify-center">
        <ShieldCheck size={12} className="text-emerald-600" />
      </div>
      <div>
        <p className="text-[10px] font-bold text-slate-800">IT Act Aligned</p>
        <p className="text-[9px] text-slate-400">Rules verified</p>
      </div>
    </div>

    <div className="absolute -top-4 -right-4 bg-white rounded-xl shadow-card border border-slate-200 px-3 py-2 flex items-center gap-2">
      <div className="w-6 h-6 bg-blue-100 rounded-lg flex items-center justify-center">
        <BarChart3 size={12} className="text-blue-600" />
      </div>
      <div>
        <p className="text-[10px] font-bold text-slate-800">Live Analysis</p>
        <p className="text-[9px] text-slate-400">AI-powered</p>
      </div>
    </div>
  </div>
);

// ─── Main Component ───────────────────────────────────────────────────────────

const LandingPage = () => {
  return (
    <div className="bg-white selection:bg-blue-100 selection:text-blue-900 overflow-x-hidden">

      {/* ─── HERO ─────────────────────────────────────────────────────────── */}
      <section className="relative min-h-[90vh] flex items-center overflow-hidden">

        {/* Background */}
        <div className="absolute inset-0 mesh-gradient pointer-events-none" />
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-blue-300/40 to-transparent" />
        <div className="absolute -top-60 -right-60 w-[600px] h-[600px] bg-blue-500/8 rounded-full filter blur-3xl pointer-events-none" />
        <div className="absolute -bottom-40 -left-40 w-[500px] h-[500px] bg-indigo-500/8 rounded-full filter blur-3xl pointer-events-none" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-violet-500/5 rounded-full filter blur-3xl pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 w-full">
          <div className="grid lg:grid-cols-2 gap-16 items-center">

            {/* Left column */}
            <div className="flex flex-col gap-8">
              {/* Eyebrow */}
              <div className="animate-slide-up" style={{ animationDelay: '0ms' }}>
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold ring-1 ring-blue-200/60 shadow-sm">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                  Powered by Income Tax Act Intelligence
                </div>
              </div>

              {/* Headline */}
              <div className="animate-slide-up" style={{ animationDelay: '80ms' }}>
                <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-slate-900 tracking-tight leading-[1.05]">
                  Find every tax benefit{' '}
                  <span className="relative">
                    <span className="text-gradient-primary">you're eligible</span>
                  </span>{' '}
                  for.
                </h1>
              </div>

              {/* Subtext */}
              <p className="text-lg sm:text-xl text-slate-500 leading-relaxed max-w-lg animate-slide-up" style={{ animationDelay: '160ms' }}>
                TaxEase intelligently maps your financial profile against the Income Tax Act to surface every deduction, exemption, and saving opportunity — explained in plain language.
              </p>

              {/* CTAs */}
              <div className="flex flex-wrap gap-3 animate-slide-up" style={{ animationDelay: '240ms' }}>
                <Link
                  to="/profile"
                  className="inline-flex items-center gap-2 px-6 py-3.5 bg-blue-600 text-white rounded-xl font-semibold shadow-lg shadow-blue-600/25 hover:bg-blue-700 hover:shadow-xl hover:shadow-blue-600/30 hover:-translate-y-0.5 transition-all duration-200 group"
                >
                  Analyze My Taxes
                  <ArrowRight size={18} className="group-hover:translate-x-0.5 transition-transform" />
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center gap-2 px-6 py-3.5 bg-white text-slate-700 rounded-xl font-semibold shadow-sm border border-slate-200 hover:border-slate-300 hover:shadow hover:-translate-y-0.5 transition-all duration-200 group"
                >
                  See How It Works
                  <ChevronDown size={16} className="group-hover:translate-y-0.5 transition-transform" />
                </a>
              </div>

              {/* Trust micro-line */}
              <div className="flex items-center gap-5 pt-2 animate-slide-up" style={{ animationDelay: '320ms' }}>
                <div className="flex items-center gap-1.5 text-slate-400 text-sm">
                  <CheckCircle2 size={14} className="text-emerald-500" />
                  <span>IT Act aligned</span>
                </div>
                <div className="flex items-center gap-1.5 text-slate-400 text-sm">
                  <CheckCircle2 size={14} className="text-emerald-500" />
                  <span>Zero hallucinations</span>
                </div>
                <div className="flex items-center gap-1.5 text-slate-400 text-sm">
                  <CheckCircle2 size={14} className="text-emerald-500" />
                  <span>Free to use</span>
                </div>
              </div>
            </div>

            {/* Right column — dashboard preview */}
            <div className="flex justify-center lg:justify-end animate-fade-in" style={{ animationDelay: '400ms' }}>
              <DashboardPreview />
            </div>

          </div>
        </div>

        {/* Bottom fade */}
        <div className="absolute bottom-0 inset-x-0 h-24 bg-gradient-to-t from-white to-transparent pointer-events-none" />
      </section>

      {/* ─── TRUST PILLARS ───────────────────────────────────────────────── */}
      <section className="relative bg-white border-y border-slate-100 py-14">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-0 md:divide-x divide-slate-100">
            {[
              {
                icon: <ShieldCheck size={22} className="text-blue-600" />,
                label: 'Income Tax Act Aligned',
                desc: 'Rules verified against official IT Act provisions',
              },
              {
                icon: <Lightbulb size={22} className="text-indigo-600" />,
                label: 'Transparent Reasoning',
                desc: 'Every recommendation is explained in plain language',
              },
              {
                icon: <Target size={22} className="text-violet-600" />,
                label: 'Zero Guesswork',
                desc: 'Deterministic rules engine, not probabilistic guessing',
              },
              {
                icon: <Users size={22} className="text-emerald-600" />,
                label: 'Built for India',
                desc: 'Designed for Indian taxpayers and the IT Act framework',
              },
            ].map((pillar) => (
              <div key={pillar.label} className="flex flex-col items-center text-center gap-3 px-6 group">
                <div className="w-10 h-10 bg-slate-50 rounded-xl flex items-center justify-center border border-slate-100 group-hover:border-blue-100 group-hover:bg-blue-50 transition-colors">
                  {pillar.icon}
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-800">{pillar.label}</p>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">{pillar.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ────────────────────────────────────────────────── */}
      <section id="how-it-works" className="bg-slate-50 py-28 relative overflow-hidden">
        <div className="absolute inset-0 mesh-gradient opacity-50 pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-xs font-bold uppercase tracking-widest text-blue-600 mb-4">How It Works</p>
            <h2 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
              From profile to savings,
              <br />
              <span className="text-gradient-primary">in minutes.</span>
            </h2>
          </div>

          {/* Steps */}
          <div className="relative">
            {/* Connecting line */}
            <div className="absolute top-10 left-[12.5%] right-[12.5%] h-px bg-gradient-to-r from-blue-200 via-indigo-300 to-violet-200 hidden lg:block" />

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                {
                  step: '01',
                  icon: <FileSearch size={22} />,
                  title: 'Create your tax profile',
                  desc: 'Enter your income, investments, rent, and insurance details in a guided form.',
                  color: 'blue',
                },
                {
                  step: '02',
                  icon: <BarChart3 size={22} />,
                  title: 'Analyze your eligibility',
                  desc: 'Our rules engine evaluates every applicable section of the Income Tax Act for you.',
                  color: 'indigo',
                },
                {
                  step: '03',
                  icon: <BrainCircuit size={22} />,
                  title: 'Get AI explanations',
                  desc: 'The AI explains why you qualify or don\'t for each deduction, in plain English.',
                  color: 'violet',
                },
                {
                  step: '04',
                  icon: <PiggyBank size={22} />,
                  title: 'Maximize your savings',
                  desc: 'Follow actionable steps to fully utilize your eligible tax benefits.',
                  color: 'emerald',
                },
              ].map((item, i) => {
                const colorMap: Record<string, string> = {
                  blue:    'bg-blue-600 shadow-lg shadow-blue-600/25',
                  indigo:  'bg-indigo-600 shadow-lg shadow-indigo-600/25',
                  violet:  'bg-violet-600 shadow-lg shadow-violet-600/25',
                  emerald: 'bg-emerald-600 shadow-lg shadow-emerald-600/25',
                };
                const ringMap: Record<string, string> = {
                  blue:    'ring-blue-100',
                  indigo:  'ring-indigo-100',
                  violet:  'ring-violet-100',
                  emerald: 'ring-emerald-100',
                };
                return (
                  <div
                    key={item.step}
                    className="flex flex-col items-center text-center gap-4 group"
                    style={{ animationDelay: `${i * 100}ms` }}
                  >
                    <div className="relative">
                      <div className={`w-20 h-20 rounded-2xl ${colorMap[item.color]} text-white flex items-center justify-center ring-4 ring-offset-4 ring-offset-slate-50 ${ringMap[item.color]} group-hover:scale-105 transition-transform duration-300`}>
                        {item.icon}
                      </div>
                      <span className="absolute -top-2 -right-2 bg-white text-slate-600 text-xs font-bold w-6 h-6 rounded-full border border-slate-200 flex items-center justify-center shadow-sm">
                        {i + 1}
                      </span>
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-slate-900 mb-2">{item.title}</h3>
                      <p className="text-sm text-slate-500 leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex justify-center mt-14">
            <Link
              to="/profile"
              className="inline-flex items-center gap-2 px-6 py-3.5 bg-blue-600 text-white rounded-xl font-semibold shadow-lg shadow-blue-600/25 hover:bg-blue-700 hover:-translate-y-0.5 transition-all duration-200 group"
            >
              Start Your Analysis
              <ArrowRight size={18} className="group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      {/* ─── FEATURE CARDS ───────────────────────────────────────────────── */}
      <section className="bg-white py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-xs font-bold uppercase tracking-widest text-blue-600 mb-4">Capabilities</p>
            <h2 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
              Built for accuracy.
              <br />
              <span className="text-gradient-primary">Designed for clarity.</span>
            </h2>
            <p className="text-lg text-slate-500 mt-4 max-w-xl mx-auto">
              Three core pillars that make TaxEaseAI the most reliable tax intelligence tool for Indian professionals.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: <FileSearch size={26} />,
                iconBg: 'from-blue-500 to-blue-600',
                iconGlow: 'shadow-blue-600/30',
                badge: 'Rules Engine',
                title: 'Deterministic Eligibility',
                desc: 'Eligibility is strictly calculated using hardcoded tax brackets and rules from the IT Act. Every output is reproducible, traceable, and verifiable — zero probabilistic guessing.',
                features: ['IT Act section mapping', 'Bracket-exact calculations', 'Reproducible results'],
                gradient: 'from-blue-50/50 to-white',
              },
              {
                icon: <BrainCircuit size={26} />,
                iconBg: 'from-violet-500 to-indigo-600',
                iconGlow: 'shadow-violet-600/30',
                badge: 'AI Layer',
                title: 'AI-Powered Explainability',
                desc: 'The TaxEase AI reads complex legal provisions and explains why you are eligible — or not — in plain, conversational English. No jargon. No confusion.',
                features: ['Plain-language reasoning', 'Section-by-section breakdown', 'Conversational Q&A'],
                gradient: 'from-violet-50/50 to-white',
              },
              {
                icon: <PiggyBank size={26} />,
                iconBg: 'from-emerald-500 to-teal-600',
                iconGlow: 'shadow-emerald-600/30',
                badge: 'Insights',
                title: 'Actionable Recommendations',
                desc: 'Get precise, step-by-step guidance on exactly where to invest to maximize your tax benefits — ranked by impact and easiness to execute.',
                features: ['Investment-specific advice', 'Ranked by impact', 'Execution roadmap'],
                gradient: 'from-emerald-50/50 to-white',
              },
            ].map((card) => (
              <div
                key={card.title}
                className={`relative bg-gradient-to-b ${card.gradient} rounded-2xl p-8 border border-slate-200/80 shadow-card hover:shadow-card-hover hover:-translate-y-1 transition-all duration-300 group overflow-hidden`}
              >
                {/* Subtle top border accent */}
                <div className={`absolute top-0 left-6 right-6 h-px bg-gradient-to-r ${card.iconBg} opacity-30`} />

                <div className="flex items-start justify-between mb-6">
                  <div className={`w-14 h-14 bg-gradient-to-br ${card.iconBg} rounded-2xl flex items-center justify-center text-white shadow-lg ${card.iconGlow} group-hover:scale-110 transition-transform duration-300`}>
                    {card.icon}
                  </div>
                  <span className={`text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full bg-gradient-to-r ${card.iconBg} text-white opacity-90`}>
                    {card.badge}
                  </span>
                </div>

                <h3 className="text-xl font-bold text-slate-900 mb-3">{card.title}</h3>
                <p className="text-slate-500 leading-relaxed text-sm mb-6">{card.desc}</p>

                <ul className="space-y-2">
                  {card.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-slate-600">
                      <CheckCircle2 size={14} className="text-emerald-500 shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FINAL CTA BAND ──────────────────────────────────────────────── */}
      <section className="relative bg-slate-950 py-28 overflow-hidden">
        <div className="absolute inset-0 mesh-gradient opacity-30 pointer-events-none" />
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-blue-600/15 rounded-full filter blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-blue-500/40 to-transparent" />

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 text-blue-400 text-xs font-semibold ring-1 ring-blue-500/20 mb-8">
            <Lock size={12} />
            Free · No account required · Instant analysis
          </div>

          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-tight mb-6">
            Stop leaving money
            <br />
            <span className="text-gradient-primary">on the table.</span>
          </h2>
          <p className="text-lg text-slate-400 leading-relaxed max-w-2xl mx-auto mb-10">
            Most Indian taxpayers miss thousands of rupees in eligible deductions every year. TaxEase finds them all — in minutes.
          </p>

          <Link
            to="/profile"
            className="inline-flex items-center gap-2.5 px-8 py-4 bg-blue-600 text-white rounded-xl font-bold text-lg shadow-lg shadow-blue-600/30 hover:bg-blue-500 hover:shadow-xl hover:shadow-blue-500/40 hover:-translate-y-0.5 transition-all duration-200 group"
          >
            Analyze My Taxes Free
            <ArrowRight size={20} className="group-hover:translate-x-0.5 transition-transform" />
          </Link>

          <p className="mt-6 text-xs text-slate-600">
            Aligned with the Income Tax Act, 1961 · Not a substitute for professional CA advice
          </p>
        </div>
      </section>

    </div>
  );
};

export default LandingPage;
