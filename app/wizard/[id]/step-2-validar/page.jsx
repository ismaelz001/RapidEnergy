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
  const [autoSaveError, setAutoSaveError] = useState(null);
  const [serverMissingFields, setServerMissingFields] = useState([]);
  const [serverErrors, setServerErrors] = useState({});
  const [rawOcrData, setRawOcrData] = useState(null); // Para el panel de debug
  const [comerciales, setComerciales] = useState([]); // Lista de comerciales
  const [selectedComercial, setSelectedComercial] = useState(''); // Comercial seleccionado

  const isTestMode = process.env.NEXT_PUBLIC_TEST_MODE === 'true';

  // QA: Blindaje de Navegación
  useEffect(() => {
    if (params.id === 'new') {
      console.error("🚩 [ERROR FLUJO] Se ha intentado acceder al Paso 2 sin un ID de factura real.");
      router.replace('/dashboard');
    }
  }, [params.id]);

  // Cargar lista de comerciales
  useEffect(() => {
    async function loadComerciales() {
      try {
        const { listUsers } = await import('@/lib/apiClient');
        const users = await listUsers({ role: 'comercial', is_active: true });
        setComerciales(users || []);
      } catch (error) {
        console.error('Error cargando comerciales:', error);
      }
    }
    loadComerciales();
  }, []);

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

        // ⭐ CALCULAR PERIODO_DIAS si falta
        let periodo_dias_calculado = data.periodo_dias;
        
        if (!periodo_dias_calculado && data.fecha_inicio && data.fecha_fin) {
          try {
            const inicio = new Date(data.fecha_inicio);
            const fin = new Date(data.fecha_fin);
            const diffMs = fin - inicio;
            const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
            if (diffDays > 0 && diffDays <= 366) {
              periodo_dias_calculado = diffDays;
              console.log(`✅ periodo_dias calculado desde fechas: ${diffDays} días`);
            }
          } catch (e) {
            console.warn('⚠️ Error calculando periodo_dias desde fechas:', e);
          }
        }
        
        const mappedData = {
          cups: data.cups || '',
          atr: data.atr || '',
          total_factura: data.total_factura || data.importe || 0,
          periodo_dias: periodo_dias_calculado || 0,  // ✅ FIX: 0 si null (número identificable como inválido)
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
          iva: data.iva ?? 0,  // ✅ FIX: 0 si null (número, no string)
          iva_porcentaje: data.iva_porcentaje != null
            ? (Number(data.iva_porcentaje) <= 1 ? Number(data.iva_porcentaje) * 100 : data.iva_porcentaje)
            : 21,  // Default 21%
          impuesto_electrico: data.impuesto_electrico ?? 0,  // ✅ FIX: 0 si null (número)
          alquiler_contador: data.alquiler_contador ?? 0,  // ✅ FIX: 0 si null
          coste_energia_actual: data.coste_energia_actual ?? '',
          coste_potencia_actual: data.coste_potencia_actual ?? ''
        };

        // Auditoría de datos en consola (QA)
        const auditKeysMap = {
          cups: 'cups',
          atr: 'atr',
          total_factura: 'total_factura',
          periodo_dias: 'periodo_dias',
          cliente: 'cliente',
          consumo_total: 'consumo_kwh',
          potencia_p1: 'potencia_p1_kw',
          potencia_p2: 'potencia_p2_kw',
          consumo_p1: 'consumo_p1_kwh',
          consumo_p2: 'consumo_p2_kwh',
          consumo_p3: 'consumo_p3_kwh',
          iva: 'iva',
          impuesto_electrico: 'impuesto_electrico'
        };

        Object.keys(mappedData).forEach(key => {
          const value = mappedData[key];
          const backendKey = auditKeysMap[key] || key;
          const fromOCR = data[backendKey] || (key === 'cliente' && data.titular);
          
          if (fromOCR) {
            console.log(`✅ ${key}: "${value}" (desde OCR: ${backendKey})`);
          } else {
            console.log(`⚠️ ${key}: "${value}" (valor por defecto/vacío)`);
          }
        });

        // ⭐ FIX P0: Merge defensivo para no pisar cambios del usuario
        // Si el usuario ya ha escrito algo, lo respetamos frente al vacío del servidor
        updateFormData({
          ...mappedData,
          periodo_dias: (formData.periodo_dias !== '' && formData.periodo_dias != null) 
            ? formData.periodo_dias 
            : mappedData.periodo_dias,
          alquiler_contador: (formData.alquiler_contador !== '' && formData.alquiler_contador != null) 
            ? formData.alquiler_contador 
            : mappedData.alquiler_contador,
        });
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
  const numberFieldKeys = new Set([
    'total_factura',
    'consumo_total',
    'potencia_p1',
    'potencia_p2',
    'consumo_p1',
    'consumo_p2',
    'consumo_p3',
    'consumo_p4',
    'consumo_p5',
    'consumo_p6',
    'iva',
    'iva_porcentaje',
    'impuesto_electrico',
    'alquiler_contador',
    'coste_energia_actual',
    'coste_potencia_actual'
    // ⚠️ NO incluir periodo_dias aquí; handleChange pasa string y buildPayload hace parseInt
  ]);
  const is3TD = form.atr === '3.0TD';
  const requiredFields = [
    'cups', 
    'atr',
    'total_factura',
    'periodo_dias',  // ⭐ OBLIGATORIO para el comparador
    'potencia_p1',
    'potencia_p2',
    'consumo_p1',
    'consumo_p2',
    'consumo_p3',
    ...(is3TD ? ['potencia_p3', 'potencia_p4', 'potencia_p5', 'potencia_p6'] : []),
    ...(is3TD ? ['consumo_p4', 'consumo_p5', 'consumo_p6'] : [])
  ];

  const fieldLabels = {
    cups: 'CUPS',
    atr: 'ATR',
    total_factura: 'Total factura',
    periodo_dias: 'Periodo (días)',  // ⭐ LABEL
    potencia_p1: 'Potencia P1',
    potencia_p2: 'Potencia P2',
    potencia_p3: 'Potencia P3',
    potencia_p4: 'Potencia P4',
    potencia_p5: 'Potencia P5',
    potencia_p6: 'Potencia P6',
    consumo_p1: 'Consumo P1',
    consumo_p2: 'Consumo P2',
    consumo_p3: 'Consumo P3',
    consumo_p4: 'Consumo P4',
    consumo_p5: 'Consumo P5',
    consumo_p6: 'Consumo P6'
  };

  const normalizeAtr = (value) => {
    if (!value) return '';
    const normalized = value.toString().trim().toUpperCase().replace(',', '.').replace(/\s+/g, '');
    return /2\.?0TD/.test(normalized) ? '2.0TD' : normalized;
  };

  const parseNumberInput = (value) => {
    if (value === '' || value === null || value === undefined) return null;
    const normalized = value.toString().replace(',', '.').replace(/\s+/g, '');
    const parsed = Number(normalized);
    return Number.isNaN(parsed) ? null : parsed;
  };

  const normalizeIvaPct = (value) => {
    const parsed = parseNumberInput(value);
    if (parsed === null) return null;
    return parsed > 1 ? parsed / 100 : parsed;
  };

  const IEE_PCT = 0.0511269632;
  const costeEnergia = parseNumberInput(form.coste_energia_actual);
  const costePotencia = parseNumberInput(form.coste_potencia_actual);
  const subtotalSinImpuestos =
    costeEnergia !== null && costePotencia !== null ? costeEnergia + costePotencia : null;
  const alquilerContador = parseNumberInput(form.alquiler_contador) ?? 0;
  const ivaPct = normalizeIvaPct(form.iva_porcentaje);
  const ieeEurCalc = subtotalSinImpuestos !== null ? subtotalSinImpuestos * IEE_PCT : null;
  const baseIvaCalc =
    subtotalSinImpuestos !== null && ieeEurCalc !== null
      ? subtotalSinImpuestos + ieeEurCalc + (alquilerContador || 0)
      : null;
  const ivaEurCalc = baseIvaCalc !== null && ivaPct !== null ? baseIvaCalc * ivaPct : null;
  
  // ⭐ VALIDACIÓN DE CONSISTENCIA DE CONSUMOS (Regla para evitar lecturas acumuladas)
  const sumaConsumos = (parseNumberInput(form.consumo_p1) || 0) + 
                       (parseNumberInput(form.consumo_p2) || 0) + 
                       (parseNumberInput(form.consumo_p3) || 0) +
                       (parseNumberInput(form.consumo_p4) || 0) +
                       (parseNumberInput(form.consumo_p5) || 0) +
                       (parseNumberInput(form.consumo_p6) || 0);
  
  const consumoTotal = parseNumberInput(form.consumo_total) || 0;
  const isConsumoInconsistent = consumoTotal > 0 && Math.abs(sumaConsumos - consumoTotal) > (consumoTotal * 0.1); // Margen 10%


  // Auto-save
  useEffect(() => {
    if (loading || !params.id || params.id === 'new') return;

    const timer = setTimeout(async () => {
      try {
        setAutoSaveStatus('saving');
        setAutoSaveError(null);
        const { updateFactura, validarFacturaComercialmente } = await import('@/lib/apiClient');
        const payload = buildPayload(formData);
        
        // 🆕 Agregar comercial_id si está seleccionado
        if (selectedComercial) {
          payload.comercial_id = parseInt(selectedComercial);
        }
        
        // PASO 1: Actualizar campos de la factura
        const result = await updateFactura(params.id, payload);
        
        // PASO 2: Validar comercialmente (activa validado_step2=True)
        // Por ahora sin ajustes comerciales (bono social, descuentos, etc.)
        await validarFacturaComercialmente(params.id, {
          ajustes_comerciales: {},
          modo: "asesor"
        });
        
        if (result && typeof result === 'object') {
          const missing = Array.isArray(result.missing_fields)
            ? result.missing_fields
            : Object.keys(result.errors || {});
          setServerMissingFields(missing);
          setServerErrors(result.errors || {});
        } else {
          setServerMissingFields([]);
          setServerErrors({});
        }
        setAutoSaveStatus('saved');
      } catch (e) {
        console.error("Auto-save failed:", e);
        const message =
          e?.data?.detail?.message ||
          e?.data?.message ||
          e?.message ||
          'No se pudo guardar automaticamente';
        setAutoSaveError(message);
        setAutoSaveStatus('error');
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [formData, params.id, loading, selectedComercial]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    let nextValue = numberFieldKeys.has(name) ? value.replace(',', '.') : value;
    
    // ⭐ TRATAMIENTO ESPECIAL PERIODO (P0)
    if (name === 'periodo_dias') {
      const parsed = parseInt(value, 10);
      nextValue = isNaN(parsed) ? '' : parsed;
    }

    // ⭐ LOGGING DE TRAZABILIDAD (P0)
    if (['periodo_dias', 'iva_porcentaje', 'alquiler_contador'].includes(name)) {
      console.log(`%c [STEP2-INPUT] ${name} => ${nextValue} (type: ${typeof nextValue})`, 'background: #0ea5e9; color: #fff; padding: 2px 5px; border-radius: 3px;');
    }

    updateFormData({ [name]: nextValue });
  };

  // P6: Validación estricta y de negocio
  const isValid = (val) => {
    if (val === null || val === undefined) return false;
    if (typeof val === 'number') return val > 0;  // Para números, > 0 es válido (excluye 0)
    return String(val).trim().length > 0;  // Para strings, no vacíos
  };

  // --- HELPERS VALIDACIÓN CUPS (MVP FLEXIBLE) ---
  const normalizeCUPS = (raw) => {
    if (!raw) return '';
    return raw.trim().toUpperCase().replace(/[\s\-.]/g, '');
  };

  const isCUPSPlausible = (cups) => {
    if (!cups) return false;
    const clean = normalizeCUPS(cups);
    // Patrón flexible: ES opcional + 18-22 alfanuméricos
    return /^(ES)?[0-9A-Z]{18,22}$/.test(clean);
  };

  const buildPayload = (data) => {
    const payload = {
      cups: normalizeCUPS(data.cups) || null,
      atr: normalizeAtr(data.atr) || null,
      consumo_kwh: parseNumberInput(data.consumo_total),
      potencia_p1_kw: parseNumberInput(data.potencia_p1),
      potencia_p2_kw: parseNumberInput(data.potencia_p2),
      consumo_p1_kwh: parseNumberInput(data.consumo_p1),
      consumo_p2_kwh: parseNumberInput(data.consumo_p2),
      consumo_p3_kwh: parseNumberInput(data.consumo_p3),
      consumo_p4_kwh: parseNumberInput(data.consumo_p4),
      consumo_p5_kwh: parseNumberInput(data.consumo_p5),
      consumo_p6_kwh: parseNumberInput(data.consumo_p6),
      iva: ivaEurCalc !== null ? Number(ivaEurCalc.toFixed(4)) : undefined,
      iva_porcentaje: parseNumberInput(data.iva_porcentaje),
      impuesto_electrico: ieeEurCalc !== null ? Number(ieeEurCalc.toFixed(4)) : undefined,
      alquiler_contador: parseNumberInput(data.alquiler_contador),
      total_factura: parseNumberInput(data.total_factura),
      coste_energia_actual: parseNumberInput(data.coste_energia_actual),
      coste_potencia_actual: parseNumberInput(data.coste_potencia_actual),
      periodo_dias: Number.isFinite(parseInt(data.periodo_dias, 10))
        ? parseInt(data.periodo_dias, 10)
        : null,
    };
    
    // ✅ DEBUG LOG con tipos
    console.log("%c [STEP2-PAYLOAD-NORMALIZED] ", "background: #10b981; color: #fff; padding: 2px 6px; border-radius: 3px;", {
      periodo_dias: { value: payload.periodo_dias, type: typeof payload.periodo_dias },
      iva: { value: payload.iva, type: typeof payload.iva },
      iva_porcentaje: { value: payload.iva_porcentaje, type: typeof payload.iva_porcentaje },
      impuesto_electrico: { value: payload.impuesto_electrico, type: typeof payload.impuesto_electrico },
      alquiler_contador: { value: payload.alquiler_contador, type: typeof payload.alquiler_contador },
    });
    return payload;
  };

  const allFields = Object.keys(form);
  const completedFields = allFields.filter(key => isValid(form[key])).length;
  const missingFields = requiredFields.filter(key => !isValid(form[key]));
  const missingFieldLabels = missingFields.map(field => fieldLabels[field] || field);
  const serverMissingFieldLabels = serverMissingFields.map(field => fieldLabels[field] || field);

  // Bloquear si faltan los campos mínimos de 2.0TD
  const criticalComplete = missingFields.length === 0;

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
          missingFields={missingFieldLabels}
        />

        {/* Auto-save status */}
        <div className="flex justify-end">
          <span className={`text-xs ${autoSaveStatus === 'error' ? 'text-rojo-error' : 'text-gris-secundario'}`}>
            {autoSaveStatus === 'saving'
              ? '☁️ Guardando...'
              : autoSaveStatus === 'error'
                ? '⚠️ Error al guardar'
                : '☁️ Guardado automático'}
          </span>
        </div>
        {autoSaveError && (
          <div className="bg-rojo-error/5 border border-rojo-error/20 rounded-lg p-3 text-xs text-rojo-error">
            {autoSaveError}
          </div>
        )}

        {serverMissingFieldLabels.length > 0 && (
          <div className="bg-ambar-alerta/10 border border-ambar-alerta/30 rounded-lg p-3">
            <p className="text-xs font-semibold text-ambar-alerta">Checklist backend</p>
            <ul className="mt-2 space-y-1 text-xs text-gris-texto">
              {serverMissingFieldLabels.map((label) => (
                <li key={label} className="flex items-center gap-2">
                  <span className="text-ambar-alerta">[ ]</span>
                  <span>Falta {label}</span>
                </li>
              ))}
            </ul>
            {Object.keys(serverErrors).length > 0 && (
              <p className="text-[11px] text-gris-secundario mt-2">
                {Object.values(serverErrors).join(' · ')}
              </p>
            )}
          </div>
        )}

        {/* Campos críticos (Datos principales) */}
        <div className="card">
          <div className="flex items-center gap-2 mb-6 p-2 bg-blue-500/5 rounded-lg border border-blue-500/10">
            <span className="text-xl">📝</span>
            <h3 className="text-lg font-bold text-white">
              Datos principales
            </h3>
          </div>
          <div className="space-y-6">
            <div>
              <label htmlFor="cups" className="label text-white">
                CUPS <span className="text-xs text-blue-400 ml-1">*</span>
                <span className="text-[#94A3B8] font-normal text-xs ml-2">(Código Universal)</span>
              </label>
              <Input
                id="cups"
                name="cups"
                value={form.cups || ''}
                onChange={handleChange}
                onBlur={(e) => {
                  const clean = normalizeCUPS(e.target.value);
                  if (clean !== e.target.value) {
                    updateFormData({ cups: clean });
                  }
                }}
                validated={isValid(form.cups) && isCUPSPlausible(form.cups)}
                error={!isValid(form.cups) || (form.cups && !isCUPSPlausible(form.cups))}
                errorMessage={!isValid(form.cups) ? "CUPS es obligatorio" : "Formato no estándar (permitido pero verifica)"}
                placeholder="ES ---"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4 border-t border-[rgba(255,255,255,0.05)]">
              <div>
                <label htmlFor="atr" className="label text-white">
                  ATR <span className="text-xs text-blue-400 ml-1">*</span>
                </label>
                <Input
                  id="atr"
                  name="atr"
                  value={form.atr || ''}
                  onChange={handleChange}
                  onBlur={(e) => {
                    const normalized = normalizeAtr(e.target.value);
                    if (normalized !== e.target.value) {
                      updateFormData({ atr: normalized });
                    }
                  }}
                  validated={isValid(form.atr)}
                  placeholder="---"
                />
              </div>

              <div>
                <label htmlFor="total_factura" className="label text-white">
                  Total factura (€) <span className="text-xs text-blue-400 ml-1">*</span>
                </label>
                <Input
                  id="total_factura"
                  name="total_factura"
                  type="number"
                  step="0.01"
                  value={form.total_factura || ''}
                  onChange={handleChange}
                  validated={isValid(form.total_factura)}
                  placeholder="---"
                />
              </div>

              {/* ⭐ CRÍTICO: Campo visible para periodo_dias */}
              <div>
                <label htmlFor="periodo_dias" className="label text-white">
                  Periodo (días) <span className="text-xs text-blue-400 ml-1">*</span>
                </label>
                <Input
                  id="periodo_dias"
                  name="periodo_dias"
                  type="number"
                  step="1"
                  min="1"
                  max="366"
                  value={form.periodo_dias || ''}
                  onChange={handleChange}
                  validated={isValid(form.periodo_dias)}
                  error={!isValid(form.periodo_dias)}
                  errorMessage="Periodo es obligatorio"
                  placeholder="Ej: 30"
                />
              </div>
            </div>

            <div className="pt-4 border-t border-[rgba(255,255,255,0.05)]">
              {/* Additional Client Fields... */}
              <label htmlFor="cliente" className="label text-white">
                Cliente
              </label>
              <Input
                id="cliente"
                name="cliente"
                value={form.cliente || ''}
                onChange={handleChange}
                validated={isValid(form.cliente)}
                placeholder="---"
              />
            </div>

            {/* 🆕 Selector de Comercial Responsable */}
            <div className="pt-4 border-t border-[rgba(255,255,255,0.05)]">
              <label htmlFor="comercial" className="label text-white">
                Comercial Responsable
                <span className="text-[#94A3B8] font-normal text-xs ml-2">(Gestiona este cliente)</span>
              </label>
              <select
                id="comercial"
                name="comercial"
                value={selectedComercial}
                onChange={(e) => setSelectedComercial(e.target.value)}
                className="w-full px-4 py-3 bg-[#1E293B] border border-[rgba(255,255,255,0.1)] rounded-lg text-[#F1F5F9] focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              >
                <option value="">Seleccionar comercial...</option>
                {comerciales.map((comercial) => (
                  <option key={comercial.id} value={comercial.id}>
                    {comercial.name} ({comercial.email})
                  </option>
                ))}
              </select>
              {comerciales.length === 0 && (
                <p className="text-xs text-ambar-alerta mt-1">
                  No hay comerciales disponibles. Crea uno en Panel CEO → Colaboradores.
                </p>
              )}
            </div>

            <div className="pt-4 border-t border-[rgba(255,255,255,0.05)]">
              <label htmlFor="consumo_total" className="label text-white">
                Consumo total (kWh)
              </label>
              <Input
                id="consumo_total"
                name="consumo_total"
                type="number"
                step="0.01"
                value={form.consumo_total || ''}
                onChange={handleChange}
                validated={isValid(form.consumo_total)}
                placeholder="---"
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
              <h4 className="text-lg font-semibold text-[#F1F5F9] mb-4">
                Potencia {form.atr === '3.0TD' ? 'P1-P6' : 'P1-P2'}
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {(form.atr === '3.0TD' ? ['p1', 'p2', 'p3', 'p4', 'p5', 'p6'] : ['p1', 'p2']).map((p) => (
                  <div key={p}>
                    <label htmlFor={`potencia_${p}`} className="label text-[#F1F5F9]">
                      Potencia {p.toUpperCase()} (kW)
                    </label>
                    <Input
                      id={`potencia_${p}`}
                      name={`potencia_${p}`}
                      type="number"
                      step="0.01"
                      value={form[`potencia_${p}`]}
                      onChange={handleChange}
                      validated={isValid(form[`potencia_${p}`])}
                      placeholder="0"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Consumo por periodos */}
            <div className="bg-[#0F172A] border border-white/8 rounded-[12px] p-5">
              <h4 className="text-lg font-semibold text-[#F1F5F9] mb-4">
                Consumo {form.atr === '3.0TD' ? 'P1-P6' : 'P1-P3'}
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {(form.atr === '3.0TD' ? ['p1', 'p2', 'p3', 'p4', 'p5', 'p6'] : ['p1', 'p2', 'p3']).map((p) => (
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
              {isConsumoInconsistent && (
                <div className="mt-4 p-3 bg-rojo-error/10 border border-rojo-error/20 rounded-lg flex items-center gap-3">
                  <span className="text-xl">⚠️</span>
                  <div>
                    <p className="text-xs font-bold text-rojo-error uppercase">Aviso de Consistencia</p>
                    <p className="text-[11px] text-white">
                      La suma de periodos ({sumaConsumos.toFixed(2)} kWh) no coincide con el total ({consumoTotal.toFixed(2)} kWh). 
                      Verifica si el OCR ha leído "Lecturas" en lugar de "Consumos".
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Desglose Baseline (E+P) */}
            <div className="bg-[#0F172A] border border-white/8 rounded-[12px] p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-lg">📊</span>
                <h4 className="text-lg font-semibold text-[#F1F5F9]">Desglose Línea Base (E+P)</h4>
              </div>
              <p className="text-xs text-gris-secundario mb-4">
                Estos valores se usan para el "Ahorro Estructural" en el PDF. Si están vacíos, el sistema los estimará proporcionalmente.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="coste_energia_actual" className="label text-[#F1F5F9]">
                    Coste Energía Actual (€)
                  </label>
                  <Input
                    id="coste_energia_actual"
                    name="coste_energia_actual"
                    type="number"
                    step="0.01"
                    value={form.coste_energia_actual || ''}
                    onChange={handleChange}
                    validated={isValid(form.coste_energia_actual)}
                    placeholder="13.14"
                  />
                </div>
                <div>
                  <label htmlFor="coste_potencia_actual" className="label text-[#F1F5F9]">
                    Coste Potencia Actual (€)
                  </label>
                  <Input
                    id="coste_potencia_actual"
                    name="coste_potencia_actual"
                    type="number"
                    step="0.01"
                    value={form.coste_potencia_actual || ''}
                    onChange={handleChange}
                    validated={isValid(form.coste_potencia_actual)}
                    placeholder="18.38"
                  />
                </div>
              </div>
            </div>

            {/* Impuestos */}
            <div className="bg-[#0F172A] border border-white/8 rounded-[12px] p-5">
              <h4 className="text-lg font-semibold text-[#F1F5F9] mb-4">Impuestos</h4>
              <div className="space-y-4">
                {/* IVA Section */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="iva" className="label text-[#F1F5F9]">
                      IVA (EUR)
                      <span className="text-xs text-[#94A3B8] ml-2">(se calcula con base imponible)</span>
                    </label>
                    <Input
                      id="iva"
                      name="iva"
                      type="number"
                      step="0.01"
                      value={ivaEurCalc !== null ? ivaEurCalc.toFixed(2) : ''}
                      readOnly={true}
                      validated={ivaEurCalc !== null}
                      placeholder="Se calcula"
                    />
                  </div>
                  <div>
                    <label htmlFor="iva_porcentaje" className="label text-[#F1F5F9]">
                      IVA (%) *
                    </label>
                    <select
                      id="iva_porcentaje"
                      name="iva_porcentaje"
                      value={form.iva_porcentaje || 21}
                      onChange={handleChange}
                      className="w-full px-4 py-3 bg-[#1E293B] border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                    >
                      <option value="21">21%</option>
                      <option value="10">10%</option>
                      <option value="4">4%</option>
                    </select>
                  </div>
                </div>

                {/* Impuesto Eléctrico */}
                <div>
                  <label htmlFor="impuesto_electrico" className="label text-[#F1F5F9]">
                    Impuesto eléctrico (€)
                    <span className="text-xs text-[#94A3B8] ml-2">(5.11269632% fijo)</span>
                  </label>
                  <Input
                    id="impuesto_electrico"
                    name="impuesto_electrico"
                    type="number"
                    step="0.01"
                    value={ieeEurCalc !== null ? ieeEurCalc.toFixed(2) : ''}
                    readOnly={true}
                    validated={ieeEurCalc !== null}
                    placeholder="Se calcula"
                  />
                </div>

                {/* ⭐ Alquiler contador (para backsolve) */}
                <div>
                  <label htmlFor="alquiler_contador" className="label text-[#F1F5F9]">
                    Alquiler contador (€)
                  </label>
                  <Input
                    id="alquiler_contador"
                    name="alquiler_contador"
                    type="number"
                    step="0.01"
                    value={form.alquiler_contador || ''}
                    onChange={handleChange}
                    validated={isValid(form.alquiler_contador)}
                    placeholder="0.74"
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
              Completa los campos mínimos para comparar: {missingFieldLabels.join(', ') || 'Pendiente'}
            </p>
          </div>
        )}
      </div>
    </WizardLayout>
  );
}
