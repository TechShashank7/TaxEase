import { Link, useLocation } from 'react-router-dom';
import { Calculator, LayoutDashboard, MessageSquareText, Sparkles, ArrowRight, BookOpen } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();

  const navLinks = [
    { name: 'My Profile', path: '/profile', icon: <Calculator size={16} /> },
    { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={16} /> },
    { name: 'AI Assistant', path: '/assistant', icon: <MessageSquareText size={16} /> },
    { name: 'Act Search', path: '/rag-search', icon: <BookOpen size={16} /> },
  ];

  return (
    <nav className="bg-white/80 backdrop-blur-xl border-b border-slate-200/60 sticky top-0 z-50 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="relative w-8 h-8 flex items-center justify-center">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg group-hover:shadow-glow-blue transition-shadow duration-300" />
              <Sparkles size={16} className="relative text-white" />
            </div>
            <span className="font-bold text-[1.1rem] tracking-tight text-slate-900">
              TaxEase<span className="text-blue-600">AI</span>
            </span>
          </Link>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`flex items-center gap-2 px-3.5 py-2 text-sm font-medium transition-all duration-200 rounded-lg ${
                    isActive
                      ? 'text-blue-700 bg-blue-50 shadow-sm ring-1 ring-blue-500/15'
                      : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  {link.icon}
                  <span>{link.name}</span>
                </Link>
              );
            })}
          </div>

          {/* Mobile Nav Links */}
          <div className="flex md:hidden items-center gap-1">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`p-2 transition-all duration-200 rounded-lg ${
                    isActive
                      ? 'text-blue-700 bg-blue-50'
                      : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  {link.icon}
                </Link>
              );
            })}
          </div>

          {/* CTA */}
          <Link
            to="/profile"
            className="hidden md:flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-all duration-200 group"
          >
            Get Started
            <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
