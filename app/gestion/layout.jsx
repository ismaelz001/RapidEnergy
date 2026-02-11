"use client";

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { getUserRole, canAccessGestion } from '@/lib/auth';

export default function GestionLayout({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const [userName, setUserName] = useState("");
  const [userRole, setUserRole] = useState("");
  
  // Protección de ruta + cargar info usuario
  useEffect(() => {
    const role = getUserRole();
    const name = typeof window !== 'undefined' ? localStorage.getItem('user_name') || 'Usuario' : 'Usuario';
    
    if (!canAccessGestion(role)) {
      router.push('/login');
      return;
    }
    
    setUserName(name);
    setUserRole(role);
  }, [router]);
  
  const handleLogout = () => {
    if (confirm('¿Seguro que quieres cerrar sesión?')) {
      localStorage.removeItem('user_id');
      localStorage.removeItem('user_role');
      localStorage.removeItem('user_email');
      localStorage.removeItem('user_name');
      router.push('/');
    }
  };
  
  const tabs = [
    { id: 'resumen', label: 'Resumen', href: '/gestion/resumen' },
    { id: 'casos', label: 'Casos', href: '/gestion/casos' },
    { id: 'comisiones', label: 'Comisiones', href: '/gestion/comisiones' },
    { id: 'pagos', label: 'Pagos', href: '/gestion/pagos' },
    { id: 'colaboradores', label: 'Colaboradores', href: '/gestion/colaboradores' },
  ];
  
  return (
    <div className="flex flex-col gap-8">
      {/* Header con tabs y botón salir */}
      <div className="flex flex-col gap-6 border-b border-[rgba(255,255,255,0.08)]">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white tracking-tight">Gestión</h1>
          
          {/* Usuario y salir */}
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-semibold text-white">{userName}</p>
              <p className="text-xs text-[#64748B] uppercase">{userRole}</p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.1)] text-[#94A3B8] hover:text-white rounded-lg text-sm font-semibold transition-colors"
            >
              Salir
            </button>
          </div>
        </div>
        
        <div className="flex items-center gap-8 translate-y-[1px]">
          {tabs.map((tab) => (
            <a
              key={tab.id}
              href={tab.href}
              className={`
                pb-4 text-sm font-semibold transition-all border-b-2
                ${pathname === tab.href
                  ? 'text-[#F1F5F9] border-[#1E3A8A]' 
                  : 'text-[#94A3B8] border-transparent hover:text-white'
                }
              `}
            >
              {tab.label}
            </a>
          ))}
        </div>
      </div>
      
      {/* Contenido de la página */}
      {children}
    </div>
  );
}
