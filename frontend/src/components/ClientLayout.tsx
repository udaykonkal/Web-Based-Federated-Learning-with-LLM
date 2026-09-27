import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';

export const ClientLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#202124] flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
};
