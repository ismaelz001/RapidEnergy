"use client";

import { useState, useEffect } from 'react';
import Link from "next/link";
import Button from '../components/Button';
import Badge from '../components/Badge';
import { listFacturas } from '@/lib/apiClient';

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState('casos');
  const [showKPIs, setShowKPIs] = useState(false);
  const [casos, setCasos] = useState([]);
  const [loading, setLoading] = useState(true);

  // QA: Checklist de Bienvenida en Consola (Preserved)
  useEffect(() => {
    if (process.env.NEXT_PUBLIC_TEST_MODE === 'true') {
      console.log(`%c 🛡️ RapidEnergy QA Checklist 🛡️`, 'color: #10b981; font-weight: bold; font-size: 14px;');
    }
  }, []);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await listFacturas();
        const mappedCasos = data.map(f => ({
          id: f.id,
          cliente: f.cliente?.nombre || `CUPS: ${f.cups?.slice(-6) || '---'}`,
          estado: f.estado_factura || 'pendiente_datos',
          href: f.estado_factura === 'pendiente_datos' 
            ? `/wizard/${f.id}/step-2-validar` 
            : `/wizard/${f.id}/step-3-comparar`
        }));
        setCasos(mappedCasos);
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const renderEstadoInfo = (caso) => {
    switch (caso.estado) {
      case 'pendiente_datos':
        return {
          badge: <Badge variant="pendiente">Validar datos</Badge>,
          actionLabel: 'Validar →',
          variant: 'primary' // Changed to primary for better UX
        };
      case 'lista_para_comparar':
        return {
          badge: <Badge variant="seleccionada">Listo para comparar</Badge>,
          actionLabel: 'Comparar →',
          variant: 'primary'
        };
      case 'oferta_seleccionada':
        return {
          badge: <Badge variant="completada">Oferta elegida</Badge>,
          actionLabel: 'Generar PDF →',
          variant: 'primary'
        };
      default:
        return {
          badge: <Badge variant="pendiente">Pendiente</Badge>,
          actionLabel: 'Continuar',
          variant: 'secondary'
        };
    }
  };

  const kpis = [
    { label: 'Facturas', value: casos.length },
    { label: 'Ahorro Est.', value: '---' },
    { label: 'Comisión Est.', value: '---' }
  ];

  return (
    <div className="flex flex-col gap-8">
      
      {/* Page Title & Tabs */}
      <div className="flex flex-col gap-6 border-b border-[rgba(255,255,255,0.08)]">
        <h1 className="text-3xl font-bold text-white tracking-tight">Panel de Control</h1>
        <div className="flex items-center gap-8 translate-y-[1px]">
          {['casos', 'tarifas', 'comisiones'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`
                pb-4 text-sm font-semibold transition-all border-b-2
                ${activeTab === tab 
                  ? 'text-[#F1F5F9] border-[#1E3A8A]' 
                  : 'text-[#94A3B8] border-transparent hover:text-white'
                }
              `}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* CONTENT: CASOS */}
      {activeTab === 'casos' && (
        <div className="animate-in fade-in duration-300 space-y-8">
          
          {/* Main List */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
               <h2 className="text-lg font-semibold text-white">Casos en curso</h2>
               {/* Small action if needed */}
            </div>
            
            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-blue"></div>
              </div>
            ) : casos.length > 0 ? (
              <div className="grid grid-cols-1 gap-3">
                {casos.map((caso) => {
                  const { badge, actionLabel, variant } = renderEstadoInfo(caso);
                  return (
                    <div key={caso.id} className="card flex flex-col md:flex-row items-center justify-between gap-4 py-4 hover:border-[#1E3A8A]/50 transition-colors group">
                      <div className="flex items-center gap-4 flex-1">
                        <div className="w-10 h-10 rounded-lg bg-[#0B1220] border border-white/5 flex items-center justify-center font-bold text-[#94A3B8] group-hover:text-white transition-colors">
                          {caso.id}
                        </div>
                        <div>
                          <h3 className="font-bold text-white mb-1">
                            {caso.cliente}
                          </h3>
                          {badge}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Link href={caso.href}>
                          <Button variant={variant} className="text-sm px-6 h-10">
                            {actionLabel}
                          </Button>
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="card py-16 text-center border-dashed border-2 border-[rgba(255,255,255,0.08)] bg-transparent">
                <div className="text-5xl mb-4 opacity-20">📂</div>
                <h3 className="text-lg font-bold text-white mb-2">No hay casos activos</h3>
                <p className="text-[#94A3B8] max-w-sm mx-auto mb-6">
                  Sube tu primera factura para comenzar a generar ahorros.
                </p>
                <Link href="/wizard/new/step-1-factura">
                  <Button variant="primary">Nueva Factura</Button>
                </Link>
              </div>
            )}
          </div>

          {/* Toggle KPI Footer */}
          <div className="pt-8 border-t border-[rgba(255,255,255,0.05)]">
             <button onClick={() => setShowKPIs(!showKPIs)} className="text-xs font-bold text-[#94A3B8] uppercase tracking-widest hover:text-white transition">
                {showKPIs ? 'Ocultar Resumen' : 'Ver Resumen Trimestral'}
             </button>
             {showKPIs && (
               <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 animate-in slide-in-from-top-2">
                 {kpis.map((kpi) => (
                   <div key={kpi.label} className="card p-6 border-white/5 bg-[#131C31]">
                     <div className="text-2xl font-black text-white mb-1">{kpi.value}</div>
                     <div className="text-[10px] uppercase font-bold text-zinc-500">{kpi.label}</div>
                   </div>
                 ))}
               </div>
             )}
          </div>
        </div>
      )}

      {/* CONTENT: TARIFAS (MOCK) */}
      {activeTab === 'tarifas' && (
        <div className="animate-in fade-in duration-300">
           <div className="card overflow-hidden p-0">
             <table className="w-full text-left text-sm text-[#94A3B8]">
               <thead className="bg-[#020617] text-white uppercase text-xs font-bold border-b border-white/5">
                 <tr>
                   <th className="px-6 py-4">Proveedor</th>
                   <th className="px-6 py-4">Tarifa</th>
                   <th className="px-6 py-4">Tipo</th>
                   <th className="px-6 py-4">Vigencia</th>
                   <th className="px-6 py-4">Estado</th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-white/5">
                 {[
                   { prov: 'Naturgy', name: 'Plan Industrial 24h', type: 'Indexada', vig: '12 meses', status: 'Activa' },
                   { prov: 'Iberdrola', name: 'Empresas 3.0TD', type: 'Fija', vig: '24 meses', status: 'Revisión' },
                   { prov: 'Endesa', name: 'Conecta Negocio', type: 'Mixta', vig: '12 meses', status: 'Activa' },
                 ].map((row, i) => (
                   <tr key={i} className="hover:bg-white/[0.02]">
                     <td className="px-6 py-4 font-medium text-white">{row.prov}</td>
                     <td className="px-6 py-4">{row.name}</td>
                     <td className="px-6 py-4">{row.type}</td>
                     <td className="px-6 py-4">{row.vig}</td>
                     <td className="px-6 py-4">
                       <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border ${row.status === 'Activa' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-amber-500/10 text-amber-500 border-amber-500/20'}`}>
                         {row.status}
                       </span>
                     </td>
                   </tr>
                 ))}
               </tbody>
             </table>
           </div>
        </div>
      )}

      {/* CONTENT: COMISIONES (PLACEHOLDER) */}
      {activeTab === 'comisiones' && (
        <div className="animate-in fade-in duration-300 text-center py-20">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-[#1E3A8A]/20 text-[#1E3A8A] border border-[#1E3A8A]/30 text-xs font-bold mb-4">
            EN DESARROLLO
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Tus comisiones, pronto aquí</h2>
          <p className="text-[#94A3B8] max-w-md mx-auto">
            Estamos construyendo un panel detallado para que visualices tus ganancias generadas por cada contrato cerrado.
          </p>
        </div>
      )}

    </div>
  );
}
