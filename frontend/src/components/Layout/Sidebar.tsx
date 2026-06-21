import React from 'react';
import { 
  LayoutDashboard, 
  ArrowRightLeft, 
  ShieldAlert, 
  Activity, 
  Server, 
  Terminal, 
  Settings,
  TrendingUp,
  Calculator
} from 'lucide-react';
import { cn } from '../../utils';

const navItems = [
  { name: 'Dashboard', icon: LayoutDashboard, active: true },
  { name: 'Transactions', icon: ArrowRightLeft },
  { name: 'Risk Analytics', icon: ShieldAlert },
  { name: 'Risk Calculator', icon: Calculator },
  { name: 'Monitoring', icon: Activity },
  { name: 'Infrastructure', icon: Server },
  { name: 'Logs', icon: Terminal },
  { name: 'Settings', icon: Settings },
];

type SidebarProps = {
  activePage: string;
  setActivePage: (page: string) => void;
};

export const Sidebar: React.FC<SidebarProps> = ({ activePage, setActivePage }) => {
  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 hidden md:flex flex-col h-full">
      <div className="h-16 flex items-center px-6 border-b border-slate-800">
        <TrendingUp className="w-6 h-6 text-blue-500 mr-2" />
        <span className="text-xl font-bold text-white tracking-tight">FinSight</span>
      </div>
      
      <div className="flex-1 overflow-y-auto py-6">
        <nav className="px-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.name;
            return (
              <a
                key={item.name}
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  setActivePage(item.name);
                }}
                className={cn(
                  "flex items-center px-3 py-2.5 text-sm font-medium rounded-md transition-colors",
                  isActive 
                    ? "bg-blue-600/10 text-blue-400" 
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                )}
              >
                <Icon className={cn("flex-shrink-0 w-5 h-5 mr-3", isActive ? "text-blue-500" : "text-slate-500")} />
                {item.name}
              </a>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-slate-800">
        <div className="bg-slate-800/50 rounded-lg p-4">
          <p className="text-xs text-slate-400 font-medium mb-2">System Status</p>
          <div className="flex items-center">
            <div className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-soft-pulse" />
            <span className="text-sm text-slate-300">All systems operational</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
