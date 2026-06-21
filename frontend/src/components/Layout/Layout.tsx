import React from 'react';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';

type LayoutProps = {
  children: React.ReactNode;
  activePage: string;
  setActivePage: (page: string) => void;
};

export const Layout: React.FC<LayoutProps> = ({ children, activePage, setActivePage }) => {
  return (
    <div className="flex h-screen bg-slate-950 overflow-hidden text-slate-50 font-sans">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto p-6 lg:p-8 custom-scrollbar">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
