"use client";

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { getUserRole, canAccessGestion } from '@/lib/auth';

export default function GestionLayout({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  
  // Protección de ruta
  useEffect(() => {
    const role = getUserRole();
    if (!canAccessGestion(role)) {
      router.push('/dashboard');
    }
  }, [router]);
  
  const tabs = [
    { id: 'resumen', label: 'Resumen', href: '/gestion/resumen' },
    { id: 'casos', label: 'Casos', href: '/gestion/casos' },
    { id: 'comisiones', label: 'Comisiones', href: '/gestion/comisiones' },
    { id: 'pagos', label: 'Pagos', href: '/gestion/pagos' },
    { id: 'colaboradores', label: 'Colaboradores', href: '/gestion/colaboradores' },
  ];
  
  return (
    <div className="flex flex-col gap-8">
      {/* Header con tabs */}
      <div className="flex flex-col gap-6 border-b border-[rgba(255,255,255,0.08)]">
        <h1 className="text-3xl font-bold text-white tracking-tight">Gestión</h1>
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
