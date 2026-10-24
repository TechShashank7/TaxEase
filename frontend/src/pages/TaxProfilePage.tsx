import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calculator, Loader2 } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const InputField = ({ label, name, type = "number", required = false, value, onChange }: any) => (
  <div>
    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wide mb-2">{label}</label>
    <input 
      type={type} 
      name={name} 
      value={value} 
      onChange={onChange} 
      onWheel={(e) => (e.target as HTMLElement).blur()}
      required={required}
      className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
    />
  </div>
);

const TaxProfilePage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: 'Arjun Kumar',
    age: 35,
    annual_income: 1500000,
    tax_regime: 'old',
    has_girl_child: true,
    is_metro_city: true,
    basic_salary: 600000,
    rent_paid: 200000,
    hra_received: 180000,
    sec_80c_investments: 100000,
    health_insurance_premium: 15000,
    parents_age: 65,
    parents_health_insurance_premium: 0,
    nps_contribution: 0,
    home_loan_interest: 0,
    scss_investment: 0,
    ssy_investment: 0
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as any;
    let finalValue: any = value;
    
    if (type === 'checkbox') {
      finalValue = (e.target as HTMLInputElement).checked;
    } else if (type === 'number') {
      finalValue = value === '' ? '' : Number(value);
    }
    
    setFormData(prev => ({ ...prev, [name]: finalValue }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      // Convert any empty strings to 0 for numerical fields before submitting
      const payload = { ...formData };
      Object.keys(payload).forEach(key => {
        if ((payload as any)[key] === '') {
          (payload as any)[key] = 0;
        }
      });

      const response = await fetch(`${API_BASE_URL}/api/v1/eligibility/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      
      if (!response.ok) {
        throw new Error('Failed to evaluate tax profile. Please check if the backend is running.');
      }
      
      const result = await response.json();
      localStorage.setItem('taxProfile', JSON.stringify(formData));
      localStorage.setItem('analysisResult', JSON.stringify(result));
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="max-w-4xl mx-auto px-4 py-12 animate-fade-in">
      <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden ring-1 ring-slate-900/5">
        
        <div className="bg-gradient-to-r from-blue-700 to-blue-600 px-8 py-10 text-white">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-white/10 rounded-xl backdrop-blur-sm">
              <Calculator size={28} />
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight">Tax Profile</h1>
          </div>
          <p className="text-blue-100 text-lg max-w-xl">Enter your financial details accurately. Our deterministic Rules Engine will calculate your exact benefits.</p>
        </div>
        
        {error && (
          <div className="m-8 p-4 bg-red-50 text-red-700 border border-red-200 rounded-xl flex items-center gap-3 text-sm font-medium">
            <span className="flex-shrink-0 w-2 h-2 rounded-full bg-red-600 animate-pulse" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-8 md:p-10 space-y-12">
          
          <section>
            <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs">1</span>
              Personal Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
              <InputField label="Full Name" name="name" type="text" required={true} value={formData.name} onChange={handleChange} />
              <InputField label="Age" name="age" required={true} value={formData.age} onChange={handleChange} />
              <InputField label="Total Annual Income (₹)" name="annual_income" required={true} value={formData.annual_income} onChange={handleChange} />
              
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wide mb-2">Tax Regime</label>
                <select name="tax_regime" value={formData.tax_regime} onChange={handleChange} className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none appearance-none">
                  <option value="old">Old Tax Regime</option>
                  <option value="new">New Tax Regime</option>
                </select>
              </div>
              
              <div className="md:col-span-2 flex flex-wrap gap-6 pt-2">
                <label className="flex items-center space-x-3 cursor-pointer group">
                  <input type="checkbox" name="has_girl_child" checked={formData.has_girl_child} onChange={handleChange} className="w-5 h-5 text-blue-600 focus:ring-blue-500 border-slate-300 rounded cursor-pointer transition-all" />
                  <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900 transition-colors">I have a girl child (for SSY)</span>
                </label>
                <label className="flex items-center space-x-3 cursor-pointer group">
                  <input type="checkbox" name="is_metro_city" checked={formData.is_metro_city} onChange={handleChange} className="w-5 h-5 text-blue-600 focus:ring-blue-500 border-slate-300 rounded cursor-pointer transition-all" />
                  <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900 transition-colors">I live in a Metro city (for HRA)</span>
                </label>
              </div>
            </div>
          </section>

          <hr className="border-slate-100" />

          <section>
            <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs">2</span>
              Salary & Housing
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
              <InputField label="Basic Salary (Annual) (₹)" name="basic_salary" value={formData.basic_salary} onChange={handleChange} />
              <InputField label="HRA Received (Annual) (₹)" name="hra_received" value={formData.hra_received} onChange={handleChange} />
              <InputField label="Rent Paid (Annual) (₹)" name="rent_paid" value={formData.rent_paid} onChange={handleChange} />
              <InputField label="Home Loan Interest Paid (₹)" name="home_loan_interest" value={formData.home_loan_interest} onChange={handleChange} />
            </div>
          </section>

          <hr className="border-slate-100" />

          <section>
            <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs">3</span>
              Current Investments
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6 bg-slate-50 p-6 rounded-2xl border border-slate-100">
              <InputField label="80C Investments (PF, ELSS, LIC) (₹)" name="sec_80c_investments" value={formData.sec_80c_investments} onChange={handleChange} />
              <InputField label="NPS Contribution 80CCD(1B) (₹)" name="nps_contribution" value={formData.nps_contribution} onChange={handleChange} />
              <InputField label="Health Insurance (Self/Family) (₹)" name="health_insurance_premium" value={formData.health_insurance_premium} onChange={handleChange} />
              <InputField label="Parents Age (Oldest)" name="parents_age" value={formData.parents_age} onChange={handleChange} />
            </div>
          </section>

          <div className="pt-8 border-t border-slate-200 flex justify-end">
            <button 
              type="submit" 
              disabled={isLoading} 
              className="px-8 py-4 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 transition-all disabled:opacity-70 flex items-center gap-2 shadow-sm"
            >
              {isLoading ? (
                <>
                  <Loader2 size={20} className="animate-spin" />
                  Analyzing Rules...
                </>
              ) : 'Generate Analysis'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TaxProfilePage;
