import React, { useEffect, useRef } from 'react';
import { useSimulation } from '../../context/SimulationContext';
import { Database, Server, Workflow, CheckCircle2, ArrowRight, GitBranch, PlayCircle, Box, Cpu } from 'lucide-react';
import { cn } from '../../utils';

export const InfrastructureCard = () => {
  const { metrics, isSimulating } = useSimulation();
  
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col w-full h-full">
      <h3 className="text-lg font-semibold text-white mb-6">Kubernetes Cluster Architecture</h3>
      <div className="flex-1 flex items-center justify-center relative py-8">
        <div className="flex flex-col md:flex-row items-center justify-between w-full max-w-4xl space-y-8 md:space-y-0 relative">
          
          {/* Load Balancer */}
          <div className="flex flex-col items-center z-10">
            <div className="w-16 h-16 rounded-2xl bg-blue-500/20 border border-blue-500 flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.2)] mb-3">
              <Workflow className="w-8 h-8 text-blue-400" />
            </div>
            <span className="text-sm font-medium text-slate-300">Ingress / ALB</span>
            <div className="text-xs text-emerald-400 mt-1 flex items-center">
              <span className="w-2 h-2 rounded-full bg-emerald-500 mr-1 animate-pulse"></span>
              Online
            </div>
          </div>

          {/* Connecting Line */}
          <div className="hidden md:flex flex-1 items-center justify-center px-4">
            <div className="w-full h-0.5 bg-slate-700 relative overflow-hidden">
              <div className={cn("absolute inset-y-0 left-0 bg-blue-500 transition-all", isSimulating ? "animate-[flow_0.5s_linear_infinite]" : "animate-[flow_2s_linear_infinite]")} style={{ width: '20px' }}></div>
            </div>
            <ArrowRight className="text-slate-600 absolute ml-10" />
          </div>

          {/* Analytics API */}
          <div className="flex flex-col items-center z-10">
            <div className={cn("w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-500 mb-3", isSimulating ? "bg-amber-500/20 border border-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.3)]" : "bg-indigo-500/20 border border-indigo-500")}>
              <Server className={cn("w-8 h-8", isSimulating ? "text-amber-400 animate-pulse" : "text-indigo-400")} />
            </div>
            <span className="text-sm font-medium text-slate-300">Analytics API</span>
            <span className="text-xs text-slate-500 mt-1">Pods: {Math.max(2, Math.floor(metrics.activePods / 2))}</span>
          </div>

          {/* Connecting Line */}
          <div className="hidden md:flex flex-1 items-center justify-center px-4">
            <div className="w-full h-0.5 bg-slate-700 relative overflow-hidden">
               <div className={cn("absolute inset-y-0 left-0 bg-indigo-500 transition-all", isSimulating ? "animate-[flow_0.5s_linear_infinite]" : "animate-[flow_2s_linear_infinite]")} style={{ width: '20px' }}></div>
            </div>
            <ArrowRight className="text-slate-600 absolute ml-10" />
          </div>

          {/* Risk Engine */}
          <div className="flex flex-col items-center z-10 relative">
            <div className="absolute -top-10 text-xs text-blue-400 font-mono bg-blue-900/30 px-2 py-1 rounded border border-blue-800">
              HPA Enabled
            </div>
            <div className={cn("w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-500 mb-3", isSimulating ? "bg-red-500/20 border border-red-500 shadow-[0_0_20px_rgba(239,68,68,0.4)]" : "bg-purple-500/20 border border-purple-500")}>
              <Cpu className={cn("w-8 h-8", isSimulating ? "text-red-400 animate-pulse" : "text-purple-400")} />
            </div>
            <span className="text-sm font-medium text-slate-300">Risk Engine</span>
            <span className={cn("text-xs mt-1 transition-colors", isSimulating ? "text-red-400" : "text-slate-500")}>Pods: {metrics.activePods}</span>
          </div>

          {/* Connecting Line */}
          <div className="hidden md:flex flex-1 items-center justify-center px-4">
            <div className="w-full h-0.5 bg-slate-700 relative overflow-hidden">
               <div className={cn("absolute inset-y-0 left-0 bg-purple-500 transition-all", isSimulating ? "animate-[flow_0.5s_linear_infinite]" : "animate-[flow_2s_linear_infinite]")} style={{ width: '20px' }}></div>
            </div>
            <ArrowRight className="text-slate-600 absolute ml-10" />
          </div>

          {/* Database */}
          <div className="flex flex-col items-center z-10">
            <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500 flex items-center justify-center mb-3">
              <Database className="w-8 h-8 text-emerald-400" />
            </div>
            <span className="text-sm font-medium text-slate-300">PostgreSQL</span>
            <span className="text-xs text-slate-500 mt-1">Master + 2 Replicas</span>
          </div>

        </div>
      </div>
      <style>{`
        @keyframes flow {
          0% { transform: translateX(0); opacity: 1; }
          100% { transform: translateX(100px); opacity: 0; }
        }
      `}</style>
    </div>
  );
};

export const LogsConsole = () => {
  const { logs } = useSimulation();
  const logsEndRef = useRef<HTMLDivElement>(null);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col h-[500px] w-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">System Logs</h3>
        <span className="flex items-center text-xs font-mono text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded">
          <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
          Live Tail
        </span>
      </div>
      <div className="flex-1 bg-[#0A0E17] rounded-lg border border-slate-800/50 p-4 overflow-y-auto font-mono text-sm no-scrollbar flex flex-col-reverse">
        <div ref={logsEndRef} />
        {logs.map((log, i) => (
          <div key={i} className="mb-2 break-all">
            <span className="text-slate-500 mr-2">[{new Date().toLocaleTimeString()}]</span>
            <span className={cn(
              log.includes('[WARNING]') ? 'text-amber-400' : 
              log.includes('[ERROR]') ? 'text-red-400' : 
              log.includes('HPA scaled') ? 'text-blue-400 font-semibold' : 'text-slate-300'
            )}>
              {log}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export const MonitoringCard = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg w-full">
      <h3 className="text-lg font-semibold text-white mb-6">CI/CD Pipeline Status</h3>
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-4">
        
        {[
          { name: 'GitHub', icon: GitBranch, status: 'success', time: '2m ago', desc: 'Commit a1b2c3d' },
          { name: 'Jenkins', icon: PlayCircle, status: 'success', time: '1m ago', desc: 'Build #4092' },
          { name: 'Docker Registry', icon: Box, status: 'success', time: '45s ago', desc: 'Pushed v1.4.2' },
          { name: 'Kubernetes', icon: Server, status: 'success', time: '10s ago', desc: 'Rolling Update' },
          { name: 'Production', icon: CheckCircle2, status: 'success', time: 'Just now', desc: 'Active' },
        ].map((stage, idx, arr) => (
          <React.Fragment key={stage.name}>
            <div className="flex flex-col items-center flex-1 w-full relative group">
              <div className="w-12 h-12 rounded-full bg-slate-800 border-2 border-emerald-500 flex items-center justify-center mb-3 z-10 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                <stage.icon className="w-5 h-5 text-emerald-400" />
              </div>
              <h4 className="text-sm font-medium text-slate-200">{stage.name}</h4>
              <p className="text-xs text-slate-500 mt-1">{stage.desc}</p>
              <p className="text-[10px] text-slate-600 mt-0.5">{stage.time}</p>
            </div>
            {idx < arr.length - 1 && (
              <div className="hidden md:block flex-1 h-0.5 bg-emerald-500/30 relative">
                <div className="absolute inset-0 bg-emerald-500 w-full animate-pulse opacity-50"></div>
              </div>
            )}
          </React.Fragment>
        ))}

      </div>
    </div>
  );
};

export const DevOpsSection = () => {
  return (
    <div className="space-y-6 mt-6">
      <h2 className="text-xl font-bold text-white mb-4 border-b border-slate-800 pb-2">DevOps & Infrastructure</h2>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <InfrastructureCard />
        </div>
        <div className="h-96 xl:h-auto">
          <LogsConsole />
        </div>
      </div>

      <MonitoringCard />
    </div>
  );
};
