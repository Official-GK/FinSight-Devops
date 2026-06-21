import React from 'react';
import { LineChart, Line, AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useSimulation } from '../../context/SimulationContext';
import { cn } from '../../utils';

const COLORS = ['#10B981', '#F59E0B', '#EF4444', '#7F1D1D']; // Low, Medium, High, Critical

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-800 border border-slate-700 p-3 rounded-lg shadow-xl">
        <p className="text-slate-300 text-sm mb-1">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm font-bold" style={{ color: entry.color }}>
            {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export const TransactionsChart = () => {
  const { analytics } = useSimulation();
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <h3 className="text-lg font-semibold text-white mb-4">Transactions Per Minute (Live)</h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={analytics.transactionsOverTime}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis dataKey="time" stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey="value" name="Volume" stroke="#3B82F6" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#3B82F6' }} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export const RiskTrendChart = () => {
  const { isSimulating, analytics } = useSimulation();
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <h3 className="text-lg font-semibold text-white mb-4">Average Risk Score Trend</h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={analytics.riskTrend}>
            <defs>
              <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={isSimulating ? '#EF4444' : '#F59E0B'} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={isSimulating ? '#EF4444' : '#F59E0B'} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis dataKey="time" stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} domain={[0, 100]} />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="value" name="Risk Score" stroke={isSimulating ? '#EF4444' : '#F59E0B'} strokeWidth={3} fillOpacity={1} fill="url(#colorRisk)" isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export const RiskDistributionChart = () => {
  const { analytics } = useSimulation();
  const pieData = [
    { name: 'Low Risk', value: analytics.riskDistribution?.LOW || 0 },
    { name: 'Medium Risk', value: analytics.riskDistribution?.MEDIUM || 0 },
    { name: 'High Risk', value: analytics.riskDistribution?.HIGH || 0 },
    { name: 'Critical', value: analytics.riskDistribution?.CRITICAL || 0 },
  ].filter(item => item.value > 0);

  if (pieData.length === 0) {
    pieData.push({ name: 'No Data', value: 1 });
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <h3 className="text-lg font-semibold text-white mb-4">Real-Time Risk Distribution</h3>
      <div className="h-72 flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={70}
              outerRadius={100}
              paddingAngle={5}
              dataKey="value"
              stroke="none"
              isAnimationActive={false}
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.name === 'No Data' ? '#334155' : COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: '12px', color: '#94A3B8' }}/>
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export const RecentTransactionsTable = () => {
  const { analytics } = useSimulation();
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col h-[350px]">
      <h3 className="text-lg font-semibold text-white mb-4">Recent Transactions</h3>
      <div className="flex-1 overflow-y-auto no-scrollbar pr-2">
        {analytics.recentTransactions && analytics.recentTransactions.length > 0 ? (
          <div className="space-y-3">
            {analytics.recentTransactions.slice(0, 15).map((txn: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-slate-200">{txn.transaction_type} • {txn.currency}</span>
                  <span className="text-xs text-slate-500 font-mono mt-0.5">{txn.transaction_id.split('-')[0]}</span>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm font-bold text-white">${txn.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  <span className={cn(
                    "text-xs px-2 py-1 rounded font-medium",
                    txn.risk_level === 'LOW' ? "bg-emerald-500/10 text-emerald-400" :
                    txn.risk_level === 'MEDIUM' ? "bg-amber-500/10 text-amber-400" :
                    "bg-red-500/10 text-red-400"
                  )}>
                    {txn.risk_level} ({txn.risk_score.toFixed(1)})
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-slate-500 text-sm">
            Waiting for transactions...
          </div>
        )}
      </div>
    </div>
  );
};

// Also keep the main export for backward compatibility or the dashboard view
export const FinancialCharts = () => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      <TransactionsChart />
      <RiskTrendChart />
      <RiskDistributionChart />
      <RecentTransactionsTable />
    </div>
  );
};
