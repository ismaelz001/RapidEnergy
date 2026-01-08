"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import WizardLayout from '@/app/components/wizard/WizardLayout';
import Input from '@/app/components/Input';
import ProgressBar from '@/app/components/ProgressBar';
import { useWizard } from '@/app/context/WizardContext';
import Button from '@/app/components/Button';
import Link from 'next/link';

export default function Step2ValidarPage({ params }) {
  const router = useRouter();
  const { formData, updateFormData } = useWizard();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showDebug, setShowDebug] = useState(false);
  const [autoSaveStatus, setAutoSaveStatus] = useState('saved'); 
  const [rawOcrData, setRawOcrData] = useState(null); // Para el panel de debug

  const isTestMode = process.env.NEXT_PUBLIC_TEST_MODE === 'true';

  // QA: Blindaje de Navegación
  useEffect(() => {
    if (params.id === 'new') {
      console.error("🚩 [ERROR FLUJO] Se ha intentado acceder al Paso 2 sin un ID de factura real.");
      router.replace('/dashboard');
    }
  }, [params.id]);

  // QA: Carga de Datos Real y Auditoría
  useEffect(() => {
    async function loadData() {
      if (!params.id || params.id === 'new') return;

      try {
        setLoading(true);
        const { getFactura } = await import('@/lib/apiClient');
        const data = await getFactura(params.id);
        
        if (!data) {
          setError("No se ha encontrado la factura");
          return;
        }

        setRawOcrData(data); // Guardar para debug

        console.log(`%c QA Audit - Factura #${params.id} `, 'background: #2563eb; color: #fff; font-weight: bold;');
        
        const mappedData = {
          cups: data.cups || '',
          total_factura: data.total_factura || data.importe || 0,
          cliente: data.cliente?.nombre || data.titular || '',
          consumo_total: data.consumo_kwh || 0,
          potencia_p1: data.potencia_p1_kw || 0,
          potencia_p2: data.potencia_p2_kw || 0,
          consumo_p1: data.consumo_p1_kwh || 0,
          consumo_p2: data.consumo_p2_kwh || 0,
          consumo_p3: data.consumo_p3_kwh || 0,
          consumo_p4: data.consumo_p4_kwh || 0,
          consumo_p5: data.consumo_p5_kwh || 0,
          consumo_p6: data.consumo_p6_kwh || 0,
          iva: data.iva || 0,
          impuesto_electrico: data.impuesto_electrico || 0
        };

        // Auditoría de datos en consola
        Object.keys(mappedData).forEach(key => {
          const value = mappedData[key];
          const fromOCR = data[key] || (key === 'cliente' && data.titular);
          if (fromOCR) {
            console.log(`✅ ${key}: "${value}" (desde OCR)`);
          } else {
            console.log(`⚠️ ${key}: "${value}" (valor por defecto/vacío)`);
          }
        });

        updateFormData(mappedData);
      } catch (err) {
        console.error("Error loading factura:", err);
        setError("Error al cargar los datos del servidor");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [params.id]);

  const form = formData;

  // Auto-save
  useEffect(() => {
    if (loading || !params.id || params.id === 'new') return;
    
    const timer = setTimeout(async () => {
      try {
        setAutoSaveStatus('saving');
        const { updateFactura } = await import('@/lib/apiClient');
        await updateFactura(params.id, formData);
        setAutoSaveStatus('saved');
      } catch (e) {
        console.error("Auto-save failed:", e);
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [formData, params.id, loading]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    updateFormData({ [name]: value });
  };

  // P6: Validación estricta y de negocio
  const isValid = (val) => val !== null && val !== undefined && String(val).trim().length > 0;
  
  // Bloqueo de CUPS (Regex básico España: ES + 20/22 chars)
  const isCupsValid = (cups) => {
    if (!cups) return false;
    const cleanCups = cups.replace(/\s/g, '').toUpperCase();
    return /^ES\d{16,20}[A-Z]{0,2}$/.test(cleanCups);
  };

  const criticalFields = ['cups', 'total_factura', 'cliente', 'consumo_total'];
  const allFields = Object.keys(form);
  const completedFields = allFields.filter(key => isValid(form[key])).length;
  const missingFields = criticalFields.filter(key => !isValid(form[key]));
  
  // BLOQUEO DE NEGOCIO: No permitir continuar si CUPS es falso o vacío
  const criticalComplete = criticalFields.every(key => isValid(form[key])) && isCupsValid(form.cups);

  const handleNext = () => {
    if (!criticalComplete) return;
    router.push(`/wizard/${params.id}/step-3-comparar`);
  };

  if (loading) {
    return (
      <WizardLayout currentStep={2} nextDisabled={true}>
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-azul-control"></div>
          <p className="text-gris-secundario font-medium">Cargando datos reales...</p>
        </div>
      </WizardLayout>
    );
  }

  if (error) {
    return (
      <WizardLayout currentStep={2} nextDisabled={true}>
        <div className="card text-center py-12 border-rojo-error bg-rojo-error/5">
          <span className="text-4xl mb-4 block">⚠️</span>
          <h2 className="text-xl font-bold text-gris-texto mb-2">{error}</h2>
          <p className="text-gris-secundario mb-6">Esta factura no existe o el flujo se ha roto.</p>
          <Link href="/dashboard">
            <Button variant="secondary">Volver al Panel</Button>
          </Link>
        </div>
      </WizardLayout>
    );
  }

  return (
    <WizardLayout
      currentStep={2}
      nextLabel="SIGUIENTE"
      nextDisabled={!criticalComplete}
      onNext={handleNext}
    >
      <div className="flex flex-col gap-6">
        {/* Debug Panel (Solo en TEST_MODE) */}
        {isTestMode && (
          <div className="bg-azul-control/10 border border-azul-control/20 rounded-lg p-3">
            <button 
              onClick={() => setShowDebug(!showDebug)}
              className="text-xs font-bold text-[#F1F5F9] uppercase tracking-widest flex items-center justify-between w-full"
            >
              🛠️ Panel de Debug OCR {showDebug ? '▲' : '▼'}
            </button>
            {showDebug && (
              <pre className="text-[10px] mt-2 overflow-auto max-h-40 text-azul-control bg-[#020617]/50 p-2 rounded border border-white/5">
                {JSON.stringify(rawOcrData, null, 2)}
              </pre>
            )}
          </div>
        )}

        {/* Header */}
        <div>
          <p className="text-xs uppercase tracking-wide text-gris-secundario mb-1">
            PASO 2 DE 3
          </p>
          <h1 className="text-2xl font-bold text-gris-texto">
            Valida los datos críticos
          </h1>
        </div>

        {/* Progress bar */}
        <ProgressBar
          current={completedFields}
          total={allFields.length}
          missingFields={missingFields.map(f => f.replace('_', ' '))}
        />

        {/* Auto-save status */}
        <div className="flex justify-end">
          <span className="text-xs text-gris-secundario">
            {autoSaveStatus === 'saving' ? '☁️ Guardando...' : '☁️ Guardado automático'}
          </span>
        </div>

        {/* Campos críticos (Datos principales) */}
        <div className="bg-[#0F172A] border border-white/8 rounded-[12px] p-5">
          <h3 className="text-lg font-semibold text-[#F1F5F9] mb-4">
            Datos principales
          </h3>
          <div className="space-y-4">
            <div>
              <label htmlFor="cups" className="label text-[#F1F5F9]">
                CUPS *
              </label>
              <Input
                id="cups"
                name="cups"
                value={form.cups}
                onChange={handleChange}
                validated={isCupsValid(form.cups)}
                error={form.cups && !isCupsValid(form.cups)}
                errorMessage="CUPS inválido (Debe ser ES + 20 caracteres)"
                placeholder="ES0123456789012345AB"
              />
            </div>

            <div className="pt-4 border-t border-white/[0.05]">
              <label htmlFor="total_factura" className="label text-[#F1F5F9]">
                Total factura (€) *
              </label>
              <Input
                id="total_factura"
                name="total_factura"
                type="number"
                step="0.01"
                value={form.total_factura}
                onChange={handleChange}
                validated={isValid(form.total_factura)}
                placeholder="124.50"
              />
            </div>

            <div className="pt-4 border-t border-white/5">
              <label htmlFor="cliente" className="label text-[#F1F5F9]">
                Cliente *
              </label>
              <Input
                id="cliente"
                name="cliente"
                value={form.cliente}
                onChange={handleChange}
                validated={isValid(form.cliente)}
                placeholder="Juan López Martínez"
              />
            </div>

            <div className="pt-4 border-t border-white/5">
              <label htmlFor="consumo_total" className="label text-[#F1F5F9]">
                Consumo total (kWh) *
              </label>
              <Input
                id="consumo_total"
                name="consumo_total"
                type="number"
                step="0.01"
                value={form.consumo_total}
                onChange={handleChange}
                validated={isValid(form.consumo_total)}
                placeholder="342"
              />
            </div>
          </div>
        </div>

        {/* Toggle datos avanzados */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-azul-control hover:underline text-left"
        >
          {showAdvanced ? '- Ocultar datos avanzados' : '+ Mostrar datos avanzados'}
        </button>

        {/* Datos avanzados (colapsable) */}
        {showAdvanced && (
          <div className="flex flex-col gap-6">
            {/* Potencia */}
            <div className="bg-[#0F172A] border border-white/8 rounded-[12px] p-5">
              <h4 className="text-lg font-semibold text-[#F1F5F9] mb-4">Potencia</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="potencia_p1" className="label text-[#F1F5F9]">
                    Potencia P1 (kW)
                  </label>
                  <Input
                    id="potencia_p1"
                    name="potencia_p1"
                    type="number"
                    step="0.01"
                    value={form.potencia_p1}
                    onChange={handleChange}
                    validated={isValid(form.potencia_p1)}
                    placeholder="4.6"
                  />
                </div>
                <div>
                  <label htmlFor="potencia_p2" className="label text-[#F1F5F9]">
                    Potencia P2 (kW)
                  </label>
                  <Input
                    id="potencia_p2"
                    name="potencia_p2"
                    type="number"
                    step="0.01"
                    value={form.potencia_p2}
                    onChange={handleChange}
                    validated={isValid(form.potencia_p2)}
                    placeholder="4.6"
                  />
                </div>
              </div>
            </div>

            {/* Consumo por periodos */}
            <div className="bg-[#0F172A] border border-white/8 rounded-[12px] p-5">
              <h4 className="text-lg font-semibold text-[#F1F5F9] mb-4">Consumo P1-P6</h4>
              <div className="grid grid-cols-3 gap-4">
                {['p1', 'p2', 'p3', 'p4', 'p5', 'p6'].map((p) => (
                  <div key={p}>
                    <label htmlFor={`consumo_${p}`} className="label text-[#F1F5F9]">
                      {p.toUpperCase()} (kWh)
                    </label>
                    <Input
                      id={`consumo_${p}`}
                      name={`consumo_${p}`}
                      type="number"
                      step="0.01"
                      value={form[`consumo_${p}`]}
                      onChange={handleChange}
                      validated={isValid(form[`consumo_${p}`])}
                      placeholder="0"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Impuestos */}
            <div className="bg-[#0F172A] border border-white/8 rounded-[12px] p-5">
              <h4 className="text-lg font-semibold text-[#F1F5F9] mb-4">Impuestos</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="iva" className="label text-[#F1F5F9]">
                    IVA (€) *
                  </label>
                  <Input
                    id="iva"
                    name="iva"
                    type="number"
                    step="0.01"
                    value={form.iva}
                    onChange={handleChange}
                    validated={isValid(form.iva)}
                    error={!isValid(form.iva)}
                    errorMessage={!isValid(form.iva) ? 'Campo obligatorio' : ''}
                    placeholder="26.14"
                  />
                </div>
                <div>
                  <label htmlFor="impuesto_electrico" className="label text-[#F1F5F9]">
                    Impuesto eléctrico (€)
                  </label>
                  <Input
                    id="impuesto_electrico"
                    name="impuesto_electrico"
                    type="number"
                    step="0.01"
                    value={form.impuesto_electrico}
                    onChange={handleChange}
                    validated={isValid(form.impuesto_electrico)}
                    placeholder="5.12"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Helper si faltan campos críticos */}
        {!criticalComplete && (
          <div className="bg-ambar-alerta/5 border border-ambar-alerta/20 rounded-lg p-4">
            <p className="text-sm text-ambar-alerta">
              Completa todos los campos críticos para continuar
            </p>
          </div>
        )}
      </div>
    </WizardLayout>
  );
}
