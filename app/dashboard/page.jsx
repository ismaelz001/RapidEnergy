"use client";

import { useState, useEffect } from 'react';
import Link from "next/link";
import Button from '../components/Button';
import Badge from '../components/Badge';
import { listFacturas } from '@/lib/apiClient';

export default function DashboardPage() {
  const [showKPIs, setShowKPIs] = useState(false);
  // QA: Checklist de Bienvenida en Consola
  useEffect(() => {
    if (process.env.NEXT_PUBLIC_TEST_MODE === 'true') {
      console.log(`
%c 🛡️ RapidEnergy QA Checklist 🛡️ 
---------------------------------
1. [ ] Sube factura A -> Verifica ID real en URL.
2. [ ] Sube factura B -> Verifica datos distintos.
3. [ ] Re-sube factura A -> Verifica error 409 (Duplicado).
4. [ ] Step 2: Abre "🛠️ Panel Debug OCR" para auditar.
5. [ ] Step 2: Intenta saltar CUPS vacío (Debe estar bloqueado).
---------------------------------
      `, 'color: #10b981; font-weight: bold; font-size: 14px;');
    }
  }, []);

  const [casos, setCasos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await listFacturas();
        // Mapear facturas de la base de datos al formato de "Casos" del UI
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

  // Helper para renderizar botón y badge según estado
  const renderEstadoInfo = (caso) => {
    switch (caso.estado) {
      case 'pendiente_datos':
        return {
          badge: <Badge variant="pendiente">Validar datos</Badge>,
          actionLabel: 'Validar →',
          variant: 'secondary'
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
          actionLabel: 'Generar presupuesto →',
          variant: 'primary'
        };
      case 'presupuesto_generado':
        return {
          badge: <Badge variant="completada">Terminado</Badge>,
          actionLabel: 'Ver PDF 📄',
          variant: 'secondary'
        };
      default:
        return {
          badge: <Badge variant="pendiente">Pendiente</Badge>,
          actionLabel: 'Continuar',
          variant: 'secondary'
        };
    }
  };

  // KPIs calculados (en una fase posterior esto vendría del backend)
  const kpis = [
    { label: 'Facturas', value: casos.length },
    { label: 'Ahorro Est.', value: '---' }, // Requiere lógica de ofertas seleccionadas
    { label: 'Comisión Est.', value: '---' }
  ];

  return (
    <div className="flex flex-col gap-8 py-8">
      {/* CTA Principal: Único punto de entrada */}
      <div className="text-center bg-azul-control/5 border border-white/5 rounded-2xl p-12 shadow-2xl">
        <h1 className="text-3xl font-black text-gris-texto mb-2">Comienza un nuevo ahorro</h1>
        <p className="text-gris-secundario mb-8 max-w-md mx-auto">
          Sube una factura y deja que el sistema analice las mejores ofertas del mercado automáticamente.
        </p>
        <Link href="/wizard/new/step-1-factura">
          <Button variant="primary" className="text-xl px-16 py-5 shadow-lg shadow-azul-control/20 hover:-translate-y-1 transition-transform">
            🚀 NUEVA FACTURA
          </Button>
        </Link>
      </div>

      {/* Casos en curso */}
      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-bold text-gris-texto px-1">
          Casos en curso (Gestión del CRM)
        </h2>
        
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-azul-control"></div>
          </div>
        ) : casos.length > 0 ? (
          <div className="grid grid-cols-1 gap-3">
            {casos.map((caso) => {
              const { badge, actionLabel, variant } = renderEstadoInfo(caso);
              return (
                <div key={caso.id} className="card flex flex-col md:flex-row items-center justify-between gap-4 py-5 hover:border-azul-control transition-colors group">
                  <div className="flex items-center gap-4 flex-1">
                    <div className="w-10 h-10 rounded-full bg-gris-fondo flex items-center justify-center font-bold text-gris-secundario group-hover:bg-azul-control/10 group-hover:text-azul-control transition-colors">
                      #{caso.id.toString().slice(-2)}
                    </div>
                    <div>
                      <h3 className="font-bold text-gris-texto mb-0.5">
                        {caso.cliente}
                      </h3>
                      {badge}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Link href={caso.href}>
                      <Button variant={variant} className="text-sm px-6">
                        {actionLabel}
                      </Button>
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="card text-center py-16 bg-transparent border-dashed border-2 border-white/5 rounded-2xl">
            <div className="text-4xl mb-4 text-gris-secundario/30">📂</div>
            <p className="font-bold text-gris-texto">No hay casos activos</p>
            <p className="text-sm text-gris-secundario px-4">
              Pulsa en "Nueva Factura" para empezar a procesar y ahorrar.
            </p>
          </div>
        )}
      </div>

      {/* Resumen (colapsable) */}
      <div className="pt-4 border-t border-gris-secundario/10">
        <button
          onClick={() => setShowKPIs(!showKPIs)}
          className="flex items-center gap-2 text-sm font-semibold text-gris-secundario hover:text-azul-control transition mx-auto mb-6"
        >
          {showKPIs ? '︿ Ocultar resumen trimestral' : '﹀ Ver resumen de rendimiento'}
        </button>

        {showKPIs && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-top-4 duration-300">
            {kpis.map((kpi) => (
              <div key={kpi.label} className="card text-center p-8 bg-hover-bg border-white/5">
                <div className="text-3xl font-black text-gris-texto mb-1">
                  {kpi.value}
                </div>
                <div className="text-xs uppercase tracking-widest font-bold text-gris-secundario">
                  {kpi.label}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
