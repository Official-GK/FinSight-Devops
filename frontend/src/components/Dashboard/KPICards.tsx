import { Activity, ShieldAlert, Cpu, Server, TrendingUp, AlertTriangle } from 'lucide-react';
import { useSimulation } from '../../context/SimulationContext';
import { cn } from '../../utils';

export const KPICards = () => {
  const { metrics, isSimulating } = useSimulation();

  const cards = [
    {
      title: 'Total Transactions Processed',
      value: metrics.transactionsPerMin.toLocaleString(),
      icon: Activity,
      trend: isSimulating ? 'Spiking' : 'Stable',
      trendUp: true,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10'
    },
    {
      title: 'Requests / Sec (Live)',
      value: metrics.requestsPerSec.toFixed(1),
      icon: Activity,
      trend: isSimulating ? 'High Load' : 'Normal',
      trendUp: true,
      color: isSimulating ? 'text-red-500' : 'text-emerald-500',
      bgColor: isSimulating ? 'bg-red-500/10' : 'bg-emerald-500/10'
    },
    {
      title: 'Active K8s Pods',
      value: metrics.activePods.toString(),
      icon: Server,
      trend: isSimulating ? 'Auto-Scaling...' : 'Baseline',
      trendUp: true,
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10'
    },
    {
      title: 'Average Risk Score',
      value: metrics.averageRiskScore.toFixed(1),
      icon: ShieldAlert,
      trend: isSimulating ? 'Elevated' : 'Normal',
      trendUp: !isSimulating,
      color: metrics.averageRiskScore > 20 ? 'text-red-500' : 'text-amber-500',
      bgColor: metrics.averageRiskScore > 20 ? 'bg-red-500/10' : 'bg-amber-500/10'
    },
    {
      title: 'High Risk Transactions',
      value: metrics.highRiskTransactions.toLocaleString(),
      icon: AlertTriangle,
      trend: 'Cumulative',
      trendUp: true,
      color: 'text-red-500',
      bgColor: 'bg-red-500/10'
    },
    {
      title: 'Market Volatility Index',
      value: `${metrics.marketVolatilityIndex.toFixed(1)}%`,
      icon: TrendingUp,
      trend: isSimulating ? 'High Volatility' : 'Low Volatility',
      trendUp: true,
      color: metrics.marketVolatilityIndex > 50 ? 'text-red-500' : 'text-blue-500',
      bgColor: metrics.marketVolatilityIndex > 50 ? 'bg-red-500/10' : 'bg-blue-500/10'
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
      {cards.map((card, index) => {
        const Icon = card.icon;
        return (
          <div key={index} className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg relative overflow-hidden group">
            {/* Glossy highlight effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-slate-400 text-sm font-medium mb-1">{card.title}</p>
                <h3 className="text-2xl font-bold text-white tracking-tight">{card.value}</h3>
              </div>
              <div className={cn("p-3 rounded-lg", card.bgColor)}>
                <Icon className={cn("w-5 h-5", card.color)} />
              </div>
            </div>
            
            <div className="flex items-center text-sm">
              <span className={cn(
                "font-medium", 
                card.trend.includes('-') || card.trend.includes('Normal') || card.trend.includes('Stable') || card.trend.includes('Low') || card.trend.includes('Baseline')
                  ? "text-emerald-400" 
                  : (card.trend.includes('High') || card.trend.includes('Scaling') || card.trend.includes('Spiking') || card.trend.includes('Elevated')) ? "text-amber-400" : "text-emerald-400"
              )}>
                {card.trend}
              </span>
              <span className="text-slate-500 ml-2 text-xs">live status</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
