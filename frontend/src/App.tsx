import React, { useState } from 'react';
import { Layout } from './components/Layout/Layout';
import { KPICards } from './components/Dashboard/KPICards';
import { 
  FinancialCharts, 
  TransactionsChart, 
  RiskTrendChart, 
  RiskDistributionChart, 
  RecentTransactionsTable 
} from './components/Dashboard/FinancialCharts';
import { 
  DevOpsSection, 
  InfrastructureCard, 
  MonitoringCard, 
  LogsConsole 
} from './components/Dashboard/DevOpsSection';
import { RiskCalculator } from './components/Dashboard/RiskCalculator';
import { SimulationProvider } from './context/SimulationContext';

function AppContent() {
  const [activePage, setActivePage] = useState('Dashboard');

  const renderContent = () => {
    switch (activePage) {
      case 'Dashboard':
        return (
          <div className="space-y-6">
            <KPICards />
            <FinancialCharts />
            <DevOpsSection />
          </div>
        );
      case 'Transactions':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <TransactionsChart />
              <RecentTransactionsTable />
            </div>
          </div>
        );
      case 'Risk Analytics':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RiskTrendChart />
              <RiskDistributionChart />
            </div>
          </div>
        );
      case 'Risk Calculator':
        return (
          <div className="space-y-6 max-w-4xl mx-auto">
            <RiskCalculator />
          </div>
        );
      case 'Monitoring':
        return (
          <div className="space-y-6">
            <MonitoringCard />
          </div>
        );
      case 'Infrastructure':
        return (
          <div className="space-y-6">
            <InfrastructureCard />
          </div>
        );
      case 'Logs':
        return (
          <div className="space-y-6">
            <LogsConsole />
          </div>
        );
      default:
        return (
          <div className="flex items-center justify-center h-96 border-2 border-dashed border-slate-800 rounded-xl">
            <div className="text-center">
              <h2 className="text-xl font-medium text-slate-300 mb-2">{activePage}</h2>
              <p className="text-slate-500">This module is currently under development.</p>
            </div>
          </div>
        );
    }
  };

  return (
    <Layout activePage={activePage} setActivePage={setActivePage}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            {activePage === 'Dashboard' ? 'Executive Dashboard' : activePage}
          </h1>
          <p className="text-slate-400 text-sm mt-1">Real-Time Financial Risk Analytics Platform</p>
        </div>
        <div className="hidden sm:flex items-center bg-slate-900 border border-slate-800 rounded-lg px-4 py-2 shadow-sm">
          <span className="flex h-2 w-2 relative mr-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-sm font-medium text-slate-300">Live Data Feed</span>
        </div>
      </div>
      
      {renderContent()}
      
    </Layout>
  );
}

function App() {
  return (
    <SimulationProvider>
      <AppContent />
    </SimulationProvider>
  );
}

export default App;
