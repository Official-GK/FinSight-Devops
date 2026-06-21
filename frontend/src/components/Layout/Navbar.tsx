import React from 'react';
import { Bell, Search, UserCircle, Menu } from 'lucide-react';
import { useSimulation } from '../../context/SimulationContext';

export const Navbar = () => {
  const { isSimulating, triggerSimulation } = useSimulation();

  return (
    <header className="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-4 sm:px-6 z-10 sticky top-0">
      <div className="flex items-center">
        <button className="md:hidden text-slate-400 hover:text-slate-200 mr-4">
          <Menu className="w-6 h-6" />
        </button>
        <div className="hidden sm:flex items-center bg-slate-800/50 rounded-md px-3 py-1.5 border border-slate-700/50 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all">
          <Search className="w-4 h-4 text-slate-500 mr-2" />
          <input 
            type="text" 
            placeholder="Search transactions, pods..." 
            className="bg-transparent text-sm text-slate-200 placeholder-slate-500 focus:outline-none w-64"
          />
        </div>
      </div>

      <div className="flex items-center space-x-4 sm:space-x-6">
        <button 
          onClick={triggerSimulation}
          className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
            isSimulating 
              ? 'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 cursor-pointer shadow-[0_0_15px_rgba(239,68,68,0.3)]' 
              : 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.3)]'
          }`}
        >
          {isSimulating ? 'Demo Mode Active' : 'Demo Mode'}
        </button>
        
        <div className="flex items-center text-slate-300 hover:text-white cursor-pointer relative">
          <Bell className="w-5 h-5" />
          {isSimulating && (
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full animate-ping"></span>
          )}
          {isSimulating && (
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full"></span>
          )}
        </div>
        
        <div className="flex items-center space-x-2 cursor-pointer group">
          <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 group-hover:border-blue-500 transition-colors">
            <UserCircle className="w-5 h-5 text-slate-400 group-hover:text-blue-400" />
          </div>
          <div className="hidden sm:block text-sm">
            <p className="text-slate-200 font-medium leading-none">Admin User</p>
            <p className="text-slate-500 text-xs mt-1">DevOps Engineer</p>
          </div>
        </div>
      </div>
    </header>
  );
};
