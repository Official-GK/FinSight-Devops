import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

type SimulationState = {
  isSimulating: boolean;
  triggerSimulation: () => void;
  metrics: {
    transactionsPerMin: number;
    requestsPerSec: number;
    activePods: number;
    averageRiskScore: number;
    highRiskTransactions: number;
    cpuUsage: number;
    systemUptime: number; // in hours
    networkTraffic: number; // MB/s
    marketVolatilityIndex: number;
  };
  analytics: {
    riskDistribution: any;
    recentTransactions: any[];
    transactionsOverTime: any[];
    riskTrend: any[];
  };
  logs: string[];
};

const defaultMetrics = {
  transactionsPerMin: 0,
  requestsPerSec: 0,
  activePods: 3,
  averageRiskScore: 0,
  highRiskTransactions: 0,
  cpuUsage: 35,
  systemUptime: 99.99,
  networkTraffic: 45,
  marketVolatilityIndex: 0,
};

const SimulationContext = createContext<SimulationState | undefined>(undefined);

export const SimulationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isSimulating, setIsSimulating] = useState(false);
  const [metrics, setMetrics] = useState(defaultMetrics);
  const [analytics, setAnalytics] = useState<any>({
    riskDistribution: { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 },
    recentTransactions: [],
    transactionsOverTime: [],
    riskTrend: []
  });
  
  const [logs, setLogs] = useState<string[]>([
    "[INFO] System initialized successfully",
    "[INFO] Connected to Backend API",
  ]);

  const addLog = (msg: string) => {
    setLogs((prev) => [msg, ...prev].slice(0, 50));
  };

  // Poll backend for real data
  useEffect(() => {
    const fetchRealData = async () => {
      const summary = await api.getDashboardSummary();
      const analData = await api.getDashboardAnalytics();
      
      if (summary) {
        setMetrics(prev => ({
          ...prev,
          transactionsPerMin: summary.total_transactions, // we'll use total transactions for the main display instead
          requestsPerSec: summary.requests_per_second,
          averageRiskScore: summary.average_risk_score,
          highRiskTransactions: summary.high_risk_transactions,
          marketVolatilityIndex: summary.market_volatility_index
        }));
      }
      
      if (analData) {
        setAnalytics({
          riskDistribution: analData.risk_distribution,
          recentTransactions: analData.recent_transactions,
          transactionsOverTime: analData.transactions_over_time,
          riskTrend: analData.risk_trend
        });
      }
    };

    fetchRealData();
    const interval = setInterval(fetchRealData, 2000);
    return () => clearInterval(interval);
  }, []);

  // Infrastructure Simulation (CPU, Pods) and Load Generation
  useEffect(() => {
    let infraInterval: ReturnType<typeof setInterval>;
    let loadGeneratorInterval: ReturnType<typeof setInterval>;

    if (isSimulating) {
      addLog("[WARNING] Market Volatility Event Detected!");
      addLog("[INFO] Transaction volume spiking");
      
      let step = 0;
      
      // 1. Generate REAL traffic against the backend
      loadGeneratorInterval = setInterval(async () => {
        // Send a burst of requests
        const burstSize = Math.floor(Math.random() * 5) + 5;
        for (let i = 0; i < burstSize; i++) {
          const types = ["PAYMENT", "TRANSFER", "WITHDRAWAL", "TRADE"];
          const type = types[Math.floor(Math.random() * types.length)];
          const amount = Math.random() * 50000;
          api.analyzeTransaction(amount, type);
        }
      }, 500); // Trigger bursts every 500ms
      
      // 2. Simulate infrastructure response
      infraInterval = setInterval(() => {
        step++;
        setMetrics((prev) => {
          const newMetrics = { ...prev };
          newMetrics.cpuUsage = Math.min(98, prev.cpuUsage + Math.floor(Math.random() * 10) + 5);
          newMetrics.networkTraffic += Math.floor(Math.random() * 50) + 20;

          if (newMetrics.cpuUsage > 80 && step % 3 === 0) {
             addLog("[WARNING] CPU threshold exceeded (80%)");
          }

          if (step > 5 && newMetrics.activePods < 12 && step % 4 === 0) {
            newMetrics.activePods += 2;
            addLog(`[INFO] HPA scaled pods from ${newMetrics.activePods - 2} to ${newMetrics.activePods}`);
            newMetrics.cpuUsage = Math.max(50, newMetrics.cpuUsage - 30); // Drops when scaled
          }
          return newMetrics;
        });

      }, 2000);
      
    } else {
      // Normal tick for infrastructure
      let cooldownStep = 0;
      infraInterval = setInterval(() => {
        cooldownStep++;
        setMetrics((prev) => {
          const newMetrics = {
            ...prev,
            cpuUsage: Math.max(30, Math.min(45, prev.cpuUsage + Math.floor(Math.random() * 6) - 3)),
            networkTraffic: 45 + Math.floor(Math.random() * 10) - 5,
          };
          
          // Gradually scale down pods to simulate HPA cooldown period
          if (prev.activePods > 3 && cooldownStep % 3 === 0) {
            newMetrics.activePods = Math.max(3, prev.activePods - 2);
            if (newMetrics.activePods < prev.activePods) {
              addLog(`[INFO] HPA scaled down pods from ${prev.activePods} to ${newMetrics.activePods}`);
            }
          }
          
          return newMetrics;
        });
      }, 3000);
      
      // Baseline background traffic
      loadGeneratorInterval = setInterval(() => {
         const types = ["PAYMENT", "TRANSFER"];
         const type = types[Math.floor(Math.random() * types.length)];
         const amount = Math.random() * 5000;
         api.analyzeTransaction(amount, type);
      }, 2000);
    }

    return () => {
      clearInterval(infraInterval);
      clearInterval(loadGeneratorInterval);
    };
  }, [isSimulating]);

  const triggerSimulation = () => {
    if (!isSimulating) {
      setIsSimulating(true);
      alert("Demo Mode Active: Generating real traffic against FastAPI backend and simulating infrastructure scaling.");
    } else {
      setIsSimulating(false);
      addLog("[INFO] Demo Mode deactivated, returning to baseline traffic.");
    }
  };

  return (
    <SimulationContext.Provider value={{ isSimulating, triggerSimulation, metrics, analytics, logs }}>
      {children}
    </SimulationContext.Provider>
  );
};

export const useSimulation = () => {
  const context = useContext(SimulationContext);
  if (context === undefined) {
    throw new Error('useSimulation must be used within a SimulationProvider');
  }
  return context;
};
