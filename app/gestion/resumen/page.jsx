"use client";

import { useEffect, useState } from 'react';
import { getCeoStats, getActividadReciente } from '@/lib/apiClient';
import dynamic from 'next/dynamic';

// Lazy load Chart.js component to avoid SSR issues
const EvolucionChart = dynamic(() => import('./EvolucionChart'), { ssr: false });

export default function ResumenPage() {
  const [stats, setStats] = useState(null);
  const [actividades, setActividades] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, actividadData] = await Promise.all([
          getCeoStats(),
          getActividadReciente()
        ]);
        
        setStats(statsData.kpis);
        setActividades(actividadData.actividades || []);
      } catch (error) {
        console.error('[GESTION] Error cargando datos:', error);
      } finally {
        setLoading(false);
      }
    }
    
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#0073EC]"></div>
      </div>
    );
  }

  const kpiCards = [
    { 
      label: 'Facturas procesadas', 
      value: stats?.facturas_procesadas || 0, 
      icon: '📄',
      color: 'text-blue-400'
    },
    { 
      label: 'Ahorro generado', 
      value: `€${(stats?.ahorro_total_eur || 0).toLocaleString('es-ES')}`, 
      icon: '💰',
      color: 'text-green-400'
    },
    { 
      label: 'Comisiones pendientes', 
      value: `€${(stats?.comisiones_pendientes_eur || 0).toLocaleString('es-ES')}`, 
      icon: '⏳',
      color: 'text-yellow-400'
    },
    { 
      label: 'Asesores activos', 
      value: stats?.asesores_activos || 0, 
      icon: '👥',
      color: 'text-purple-400'
    },
  ];

  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((kpi, i) => (
          <div key={i} className="card p-6 hover:border-[#1E3A8A]/50 transition-colors">
            <div className="flex items-start justify-between mb-4">
              <span className="text-4xl">{kpi.icon}</span>
            </div>
            <div className={`text-3xl font-bold mb-1 ${kpi.color}`}>
              {kpi.value}
            </div>
            <div className="text-sm text-[#94A3B8]">{kpi.label}</div>
          </div>
        ))}
      </div>
      {/* Gráfico Evolución */}
      <div className="card">
        <h3 className="text-lg font-bold text-white mb-4">📈 Evolución Mensual</h3>
        <EvolucionChart />
      </div>
      {/* Actividad reciente */}
      {actividades.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-bold text-white mb-4">🔥 Actividad reciente</h3>
          <div className="space-y-3">
            {actividades.map((act, i) => (
              <div key={i} className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
                <div>
                  <p className="text-sm font-medium text-white">{act.descripcion}</p>
                  <p className="text-xs text-[#94A3B8]">
                    {act.cliente} {act.ahorro && `• Ahorro: ${act.ahorro}`}
                  </p>
                </div>
                <a 
                  href={`/facturas`} 
                  className="text-xs text-[#0073EC] hover:text-blue-400"
                >
                  Ver →
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {actividades.length === 0 && (
        <div className="card py-16 text-center border-dashed border-2 border-[rgba(255,255,255,0.08)] bg-transparent">
          <div className="text-5xl mb-4 opacity-20">📊</div>
          <h3 className="text-lg font-bold text-white mb-2">Sin actividad reciente</h3>
          <p className="text-[#94A3B8] max-w-sm mx-auto">
            Las facturas procesadas aparecerán aquí.
          </p>
        </div>
      )}
    </div>
  );
}
