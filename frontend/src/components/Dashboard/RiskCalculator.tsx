import React, { useState } from 'react';
import { Calculator, AlertCircle, ShieldAlert, ArrowRight, Loader2, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils';

export const RiskCalculator = () => {
  const [amount, setAmount] = useState('');
  const [transactionType, setTransactionType] = useState('TRANSFER');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const transactionTypes = [
    'PAYMENT',
    'TRANSFER',
    'WITHDRAWAL',
    'DEPOSIT',
    'TRADE',
    'REFUND'
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount || isNaN(Number(amount)) || Number(amount) <= 0) {
      setError("Please enter a valid positive amount.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.analyzeTransaction(Number(amount), transactionType);
      if (data && data.risk_score !== undefined) {
        setResult(data);
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
      <div className="flex items-center mb-6">
        <div className="bg-blue-500/10 p-2 rounded-lg mr-3">
          <Calculator className="w-5 h-5 text-blue-500" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Manual Risk Evaluation</h3>
          <p className="text-sm text-slate-400">Evaluate a single transaction instantly</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Transaction Amount (USD)
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="text-slate-500 sm:text-sm">$</span>
              </div>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2.5 pl-7 pr-4 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                placeholder="0.00"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Transaction Type
            </label>
            <div className="relative">
              <select
                value={transactionType}
                onChange={(e) => setTransactionType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2.5 px-4 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all appearance-none"
              >
                {transactionTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <ArrowRight className="w-4 h-4 text-slate-500 rotate-90" />
              </div>
            </div>
          </div>

          {error && (
            <div className="flex items-center text-sm text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20">
              <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting || !amount}
            className="w-full flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              'Calculate Risk Score'
            )}
          </button>
        </form>

        {/* Results Panel */}
        <div className="bg-slate-950/50 rounded-xl border border-slate-800/50 p-6 flex flex-col justify-center relative overflow-hidden">
          {!result && !isSubmitting && (
            <div className="text-center text-slate-500 flex flex-col items-center">
              <ShieldAlert className="w-12 h-12 mb-3 opacity-20" />
              <p>Enter transaction details to see risk evaluation.</p>
            </div>
          )}

          {isSubmitting && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-sm z-10">
              <div className="relative">
                <div className="w-16 h-16 border-4 border-blue-500/20 rounded-full"></div>
                <div className="w-16 h-16 border-4 border-blue-500 rounded-full border-t-transparent animate-spin absolute top-0 left-0"></div>
              </div>
              <p className="text-blue-400 font-medium mt-4 animate-pulse">Running risk models...</p>
            </div>
          )}

          {result && !isSubmitting && (
            <div className="animate-in fade-in zoom-in duration-300">
              <div className="text-center mb-6">
                <p className="text-slate-400 text-sm mb-1">Calculated Risk Score</p>
                <div className="flex items-end justify-center">
                  <span className={cn(
                    "text-5xl font-bold tracking-tight",
                    result.risk_level === 'LOW' ? "text-emerald-400" :
                    result.risk_level === 'MEDIUM' ? "text-amber-400" :
                    "text-red-500"
                  )}>
                    {result.risk_score.toFixed(1)}
                  </span>
                  <span className="text-slate-500 ml-1 mb-1 font-medium">/ 100</span>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-slate-900 rounded-lg border border-slate-800">
                  <span className="text-slate-400 text-sm">Risk Level</span>
                  <span className={cn(
                    "text-xs px-2.5 py-1 rounded font-bold uppercase tracking-wider",
                    result.risk_level === 'LOW' ? "bg-emerald-500/10 text-emerald-400" :
                    result.risk_level === 'MEDIUM' ? "bg-amber-500/10 text-amber-400" :
                    "bg-red-500/10 text-red-400"
                  )}>
                    {result.risk_level}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-slate-900 rounded-lg border border-slate-800">
                  <span className="text-slate-400 text-sm">Engine Latency</span>
                  <span className="text-slate-200 text-sm font-mono flex items-center">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mr-1.5" />
                    {result.engine_latency_ms.toFixed(1)} ms
                  </span>
                </div>

                <div className="flex justify-between items-center p-3 bg-slate-900 rounded-lg border border-slate-800">
                  <span className="text-slate-400 text-sm">Transaction ID</span>
                  <span className="text-slate-400 text-xs font-mono truncate max-w-[150px]" title={result.transaction_id}>
                    {result.transaction_id.split('-')[0]}...
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
