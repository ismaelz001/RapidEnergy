"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import WizardLayout from '@/app/components/wizard/WizardLayout';
import Input from '@/app/components/Input';
import ProgressBar from '@/app/components/ProgressBar';
import { useWizard } from '@/app/context/WizardContext';

export default function Step2ValidarPage({ params }) {
  const router = useRouter();
  const { formData, updateFormData } = useWizard();
  
  // Usamos el estado del contexto directamente o lo sincronizamos
  // Para inputs controlados, leer directo de formData es mejor
  const form = formData;
  const setForm = updateFormData;

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [autoSaveStatus, setAutoSaveStatus] = useState('saved'); 

  // Auto-save simulado (el contexto ya persiste en memoria)
  useEffect(() => {
    setAutoSaveStatus('saved');
  }, [form]);

  // Wrapper para mantener la firma de handleChange existente
  const handleChange = (e) => {
    const { name, value } = e.target;
    // updateFormData espera un objeto parcial, no una función callback completa si usamos el setter de useState
    // Pero nuestra impl de updateFormData hace merge: setFormData(prev => ({ ...prev, ...newData }))
    updateFormData({ [name]: value });
  };

  // Helper para validación estricta (no vacíos, no solo espacios)
  const isValid = (val) => val && String(val).trim().length > 0;

  // Validar campos críticos
  const criticalFields = ['cups', 'total_factura', 'cliente', 'consumo_total'];
  const allFields = Object.keys(form);
  const completedFields = allFields.filter(key => isValid(form[key])).length;
  // Campos faltantes (solo para debug/progress bar, excluyendo opcionales si se desea)
  const missingFields = criticalFields.filter(key => !isValid(form[key]));
  const criticalComplete = criticalFields.every(key => isValid(form[key]));

  const handleNext = () => {
    router.push(`/wizard/${params.id}/step-3-comparar`);
  };

  return (
    <WizardLayout
      currentStep={2}
      nextLabel="SIGUIENTE"
      nextDisabled={!criticalComplete}
      onNext={handleNext}
    >
      <div className="flex flex-col gap-6">
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

        {/* Campos críticos */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gris-texto mb-4">
            Campos críticos
          </h3>
          <div className="space-y-4">
            <div>
              <label htmlFor="cups" className="label">
                CUPS *
              </label>
              <Input
                id="cups"
                name="cups"
                value={form.cups}
                onChange={handleChange}
                validated={isValid(form.cups)}
                placeholder="ES0123456789012345AB"
              />
            </div>

            <div>
              <label htmlFor="total_factura" className="label">
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

            <div>
              <label htmlFor="cliente" className="label">
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

            <div>
              <label htmlFor="consumo_total" className="label">
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
          <div className="card">
            <h3 className="text-lg font-semibold text-gris-texto mb-4">
              Datos avanzados (Opcionales)
            </h3>
            <div className="space-y-6">
              {/* Potencia */}
              <div>
                <h4 className="text-sm font-medium text-gris-texto mb-3">Potencia</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="potencia_p1" className="label">
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
                    <label htmlFor="potencia_p2" className="label">
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
              <div>
                <h4 className="text-sm font-medium text-gris-texto mb-3">Consumo P1-P6 (kWh)</h4>
                <div className="grid grid-cols-3 gap-4">
                  {['p1', 'p2', 'p3', 'p4', 'p5', 'p6'].map((p) => (
                    <div key={p}>
                      <label htmlFor={`consumo_${p}`} className="label">
                        {p.toUpperCase()}
                      </label>
                      <Input
                        id={`consumo_${p}`}
                        name={`consumo_${p}`}
                        type="number"
                        step="0.01"
                        value={form[`consumo_${p}`]}
                        onChange={handleChange}
                        validated={isValid(form[`consumo_${p}`])}
                        // Quitamos error={} porque son opcionales en este contexto de UI
                        placeholder="0"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Impuestos */}
              <div>
                <h4 className="text-sm font-medium text-gris-texto mb-3">Impuestos</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="iva" className="label">
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
                    <label htmlFor="impuesto_electrico" className="label">
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
          </div>
        )}

        {/* Helper si faltan campos críticos */}
        {!criticalComplete && (
          <div className="bg-ambar-alerta/10 border border-ambar-alerta rounded-lg p-4">
            <p className="text-sm text-ambar-alerta">
              Completa todos los campos críticos para continuar
            </p>
          </div>
        )}
      </div>
    </WizardLayout>
  );
}
