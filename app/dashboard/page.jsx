"use client";

import { useState } from 'react';
import Link from "next/link";
import Button from '../components/Button';
import Badge from '../components/Badge';

export default function DashboardPage() {
  const [showKPIs, setShowKPIs] = useState(false);

  // Mock data con estados reales del CRM
  const casosEnCurso = [
    {
      id: 123,
      cliente: 'Juan López',
      estado: 'pendiente_datos',
      href: '/wizard/123/step-2-validar'
    },
    {
      id: 124,
      cliente: 'María Martínez',
      estado: 'lista_para_comparar',
      href: '/wizard/124/step-3-comparar'
    },
    {
      id: 125,
      cliente: 'Carlos Ruiz',
      estado: 'oferta_seleccionada',
      href: '/wizard/125/step-3-comparar'
    },
    {
      id: 126,
      cliente: 'Ana Belén',
      estado: 'presupuesto_generado',
      href: '/wizard/126/step-3-comparar' // En un caso real iría a ver el PDF
    }
  ];

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

  const kpis = [
    { label: 'Facturas', value: '12' },
    { label: 'Ahorro', value: '2.340€' },
    { label: 'Comisión', value: '156€' }
  ];

  return (
    <div className="flex flex-col gap-8 py-8">
      {/* CTA Principal: Único punto de entrada */}
      <div className="text-center bg-white border border-azul-control/10 rounded-2xl p-12 shadow-sm">
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
        {casosEnCurso.length > 0 ? (
          <div className="grid grid-cols-1 gap-3">
            {casosEnCurso.map((caso) => {
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
          <div className="card text-center py-12 text-gris-secundario border-dashed">
            <p>No hay casos activos. Pulsa en "Nueva Factura" para empezar.</p>
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
              <div key={kpi.label} className="card text-center p-8 bg-white border-gris-secundario/20">
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
