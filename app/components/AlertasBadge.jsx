"use client";

import { useEffect, useState } from 'react';
import { getCeoStats } from '@/lib/apiClient';
import { canAccessGestion } from '@/lib/auth';

export default function AlertasBadge() {
  const [alertasCount, setAlertasCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const [alertas, setAlertas] = useState([]);

  useEffect(() => {
    if (typeof window === 'undefined' || !canAccessGestion()) return;

    loadAlertas();
    
    // Refrescar cada 5 minutos
    const interval = setInterval(loadAlertas, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const loadAlertas = async () => {
    try {
      const stats = await getCeoStats();
      if (stats.alertas && stats.alertas.length > 0) {
        setAlertas(stats.alertas);
        setAlertasCount(stats.alertas.length);
      }
    } catch (error) {
      console.error('[ALERTAS] Error:', error);
    }
  };

  if (alertasCount === 0) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="relative p-2 text-[#94A3B8] hover:text-white transition-colors"
        title="Alertas"
      >
        🔔
        {alertasCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
            {alertasCount > 9 ? '9+' : alertasCount}
          </span>
        )}
      </button>

      {showDropdown && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowDropdown(false)}
          />
          
          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-80 bg-[#0F172A] border border-white/10 rounded-lg shadow-2xl z-50 max-h-96 overflow-y-auto">
            <div className="p-3 border-b border-white/5">
              <h3 className="font-bold text-white text-sm">
                ⚠️ Alertas ({alertasCount})
              </h3>
            </div>
            
            <div className="divide-y divide-white/5">
              {alertas.map((alerta, idx) => (
                <div key={idx} className="p-3 hover:bg-[#1E293B] transition-colors">
                  <div className="flex items-start gap-2">
                    <span className="text-xl">{alerta.icono || '⚠️'}</span>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-white mb-1">
                        {alerta.titulo}
                      </div>
                      <div className="text-xs text-[#94A3B8]">
                        {alerta.descripcion}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="p-3 border-t border-white/5 text-center">
              <a
                href="/gestion/pagos"
                className="text-xs text-[#0073EC] hover:underline"
                onClick={() => setShowDropdown(false)}
              >
                Ver todas →
              </a>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
