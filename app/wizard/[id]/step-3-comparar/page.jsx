"use client";

import { useState, useEffect } from 'react';
import WizardLayout from '@/app/components/wizard/WizardLayout';
import OfferCard from '@/app/components/OfferCard';
import { useWizard } from '@/app/context/WizardContext';
import Button from '@/app/components/Button';
import { compareFactura } from '@/lib/apiClient';
import Link from 'next/link';

// Configuración de umbrales
const UMBRAL_AHORRO_SIGNIFICATIVO = 60; // €/año
const UMBRAL_SIMILAR = 10; // €/año

export default function Step3ComparerPage({ params }) {
  const { 
    formData, 
    selectedOfferId, 
    selectOffer, 
    checkRecalculationNeeded 
  } = useWizard();

  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTotal, setCurrentTotal] = useState(0);
  const [showCommission, setShowCommission] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  // Verificar si hubo cambios en datos críticos
  const isRecalculationNeeded = checkRecalculationNeeded();

  useEffect(() => {
    async function fetchOffers() {
      if (!params.id || params.id === 'new') {
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);

        // --- B) CONSTRUIR PAYLOAD DESDE EL ESTADO DEL WIZARD (FORM DATA) ---
        const d = formData;
        
        // D) Fallback consumo_total: si es 0/null pero hay consumos por periodo, sumar
        let consumoFinal = parseFloat(d.consumo_total || 0);
        if (consumoFinal === 0) {
          const sumP = [d.consumo_p1, d.consumo_p2, d.consumo_p3, d.consumo_p4, d.consumo_p5, d.consumo_p6]
            .reduce((acc, val) => acc + parseFloat(val || 0), 0);
          if (sumP > 0) {
            console.warn(`[STEP3] Consumo total era 0, recalculando como suma de periodos: ${sumP}`);
            consumoFinal = sumP;
          }
        }

        const payload = {
          cups: d.cups || null,
          atr: d.atr || null,
          periodo_dias: Number.isFinite(parseInt(d.periodo_dias, 10))
            ? parseInt(d.periodo_dias, 10)
            : null,
          consumo_kwh: consumoFinal,
          potencia_p1_kw: parseFloat(d.potencia_p1 || 0),
          potencia_p2_kw: parseFloat(d.potencia_p2 || 0),
          potencia_p3_kw: parseFloat(d.potencia_p3 || 0),
          potencia_p4_kw: parseFloat(d.potencia_p4 || 0),
          potencia_p5_kw: parseFloat(d.potencia_p5 || 0),
          potencia_p6_kw: parseFloat(d.potencia_p6 || 0),
          consumo_p1_kwh: parseFloat(d.consumo_p1 || 0),
          consumo_p2_kwh: parseFloat(d.consumo_p2 || 0),
          consumo_p3_kwh: parseFloat(d.consumo_p3 || 0),
          consumo_p4_kwh: parseFloat(d.consumo_p4 || 0),
          consumo_p5_kwh: parseFloat(d.consumo_p5 || 0),
          consumo_p6_kwh: parseFloat(d.consumo_p6 || 0),
          iva_porcentaje: parseFloat(d.iva_porcentaje || 21),
          impuesto_electrico: parseFloat(d.impuesto_electrico || 0),
          total_factura: parseFloat(d.total_factura || 0)
        };

        //  A) LOG ANTES DEL POST (QA)
        console.log(`%c [STEP3-PRE-POST] Factura #${params.id} `, 'background: #7c3aed; color: #fff; font-weight: bold;');
        console.table({
          cups: payload.cups,
          atr: payload.atr,
          periodo: payload.periodo_dias,
          consumo_total: payload.consumo_kwh,
          total_factura: payload.total_factura
        });

        // C) VALIDACIÓN PREVIA (Evitar reventar el backend)
        if (!payload.atr) {
          throw new Error("El campo ATR es obligatorio para comparar.");
        }
        if (!payload.periodo_dias || payload.periodo_dias <= 0) {
          throw new Error("El periodo (días) es obligatorio y debe ser mayor a 0.");
        }

        // Llamada al backend pasando el payload actualizado
        const result = await compareFactura(params.id, payload);
        
        const normalizedOffers = (result.offers || []).map((offer) => {
          const id = offer.tarifa_id ?? offer.id ?? offer.provider;
          return {
            ...offer,
            id,
            commission: typeof offer.commission === 'number' ? offer.commission : 0,
          };
        });
        setOffers(normalizedOffers);
        setCurrentTotal(
          typeof result.current_total === 'number'
            ? result.current_total
            : parseFloat(formData.total_factura || 0)
        );
      } catch (err) {
        console.error("Error fetching offers:", err);
        setError(err.message || "No se pudieron generar ofertas. Verifica los datos del Paso 2.");
      } finally {
        setLoading(false);
      }
    }
    
    fetchOffers();
  }, [params.id]);

  const currentTotalDisplay = Number.isFinite(currentTotal) && currentTotal > 0
    ? currentTotal
    : parseFloat(formData.total_factura || 0);
  const selectedOffer = selectedOfferId
    ? offers.find(o => String(o.id) === String(selectedOfferId))
    : null;
  
  // Encontrar el mejor ahorro
  const maxSaving = offers.length > 0 ? Math.max(...offers.map(o => o.saving_amount)) : 0;
  const bestOffer = offers.find(o => o.saving_amount === maxSaving);
  const totalAnnualSaving = bestOffer ? (bestOffer.saving_amount * 12) : 0;

  // ⭐ DETERMINAR ESTADO UX del hero
  let heroEstado = 'sin_mejora';
  let heroTitulo = '';
  let heroMensaje = '';
  let heroColor = '';
  let heroBgColor = '';
  let showCTAs = false;

  if (totalAnnualSaving >= UMBRAL_AHORRO_SIGNIFICATIVO) {
    // Estado 1: Ahorro significativo
    heroEstado = 'ahorro_significativo';
    heroTitulo = 'Ahorro anual estimado';
    heroMensaje = '';
    heroColor = 'text-[#16A34A]';
    heroBgColor = 'bg-gradient-to-r from-[#14532D]/30 to-[#16A34A]/5 border-[#16A34A]/30';
    showCTAs = false;
  } else if (totalAnnualSaving > 0 && totalAnnualSaving < UMBRAL_AHORRO_SIGNIFICATIVO) {
    // Estado 2: Ahorro bajo
    heroEstado = 'ahorro_bajo';
    heroTitulo = 'El ahorro es mínimo';
    heroMensaje = 'La diferencia de precio es muy pequeña. No recomendamos cambiar de tarifa en este momento.';
    heroColor = 'text-[#3B82F6]';
    heroBgColor = 'bg-gradient-to-r from-[#1E3A8A]/20 to-[#3B82F6]/5 border-[#3B82F6]/30';
    showCTAs = false;
  } else {
    // Estado 3: Sin mejora
    heroEstado = 'sin_mejora';
    heroTitulo = 'Tu tarifa actual es competitiva';
    heroMensaje = 'No hemos encontrado ninguna tarifa más barata para tu consumo actual. Tu coste ya está bien optimizado.';
    heroColor = 'text-[#64748B]';
    heroBgColor = 'bg-gradient-to-r from-[#334155]/20 to-[#64748B]/5 border-[#64748B]/30';
    showCTAs = true;
  }
  
  const isPartialOffer = (offer) => (
    offer?.tag === 'partial' || offer?.breakdown?.modo_potencia === 'sin_potencia'
  );

  const handleSelectOffer = (offer) => {
    if (isPartialOffer(offer)) return;
    selectOffer(offer.id);
  };

  const handleGeneratePresupuesto = async () => {
    if (isRecalculationNeeded || !selectedOffer) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // ENTREGABLE 3: Conectar Step 3 con backend real
      // 1) Guardar selección de oferta
      const { selectOffer: saveOffer, downloadPresupuestoPDF } = await import('@/lib/apiClient');
      
      await saveOffer(params.id, {
        provider: selectedOffer.provider,
        plan_name: selectedOffer.plan_name,
        tarifa_id: selectedOffer.tarifa_id,
        estimated_total: selectedOffer.estimated_total,
        saving_amount: selectedOffer.saving_amount,
        saving_percent: selectedOffer.saving_percent,
        ahorro_estructural: selectedOffer.ahorro_estructural,
        precio_medio_estructural: selectedOffer.precio_medio_estructural,
        coste_diario_estructural: selectedOffer.coste_diario_estructural,
        commission: selectedOffer.commission || 0,
        tag: selectedOffer.tag,
        breakdown: selectedOffer.breakdown
      });
      
      // 2) Descargar PDF
      const pdfBlob = await downloadPresupuestoPDF(params.id);
      
      // Crear link de descarga
      const url = window.URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `presupuesto_factura_${params.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      // 3) Mostrar modal de éxito SOLO si todo fue bien
      setShowSuccessModal(true);
      
    } catch (err) {
      console.error("Error generando presupuesto:", err);
      setError(err.message || "No se pudo generar el presupuesto. Por favor, intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmRecalculation = () => {
    selectOffer(null); 
  };

  return (
    <>
      <WizardLayout
        currentStep={3}
        nextLabel="GENERAR PRESUPUESTO"
        nextDisabled={!selectedOffer || isRecalculationNeeded || loading}
        onNext={handleGeneratePresupuesto}
        showGenerateButton={true}
      >
        <div className="flex flex-col gap-6">
          {/* Header */}
          <div>
            <p className="text-xs uppercase tracking-wide text-gris-secundario mb-1">
              PASO 3 DE 3
            </p>
            <h1 className="text-2xl font-bold text-gris-texto">
              Elige la mejor oferta
            </h1>
          </div>

          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-azul-control"></div>
              <p className="text-gris-secundario font-medium">Calculando las mejores ofertas del mercado...</p>
            </div>
          ) : error ? (
            <div className="bg-rojo-error/5 border border-rojo-error rounded-xl p-8 text-center">
              <span className="text-4xl mb-4 block">❌</span>
              <h3 className="text-lg font-bold text-gris-texto mb-2">Algo ha fallado</h3>
              <p className="text-gris-secundario mb-6">{error}</p>
              <Link href={`/wizard/${params.id}/step-2-validar`}>
                <Button variant="secondary">Revisar datos del Paso 2</Button>
              </Link>
            </div>
          ) : (
            <>
              {/* Banner de Recálculo */}
              {isRecalculationNeeded && (
                <div className="bg-ambar-alerta/10 border border-ambar-alerta rounded-lg p-4 flex flex-col md:flex-row items-center justify-between gap-4 animate-pulse">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">⚠️</span>
                    <div>
                      <h3 className="font-bold text-ambar-alerta">Hemos detectado cambios en la factura</h3>
                      <p className="text-sm text-gris-texto">
                        Los valores de las ofertas han sido recalculados. Por favor, revisa y confirma tu selección.
                      </p>
                    </div>
                  </div>
                  <Button 
                    variant="secondary" 
                    onClick={handleConfirmRecalculation}
                    className="bg-transparent border-ambar-alerta text-ambar-alerta hover:bg-ambar-alerta/10 whitespace-nowrap"
                  >
                    Revisar ofertas
                  </Button>
                </div>
              )}

              {/* ⭐ Hero CONDICIONAL según estado */}
              <div className={`border rounded-2xl p-8 text-center shadow-lg ${heroBgColor}`}>
                <span className={`text-sm font-bold tracking-widest uppercase mb-1 block ${heroColor}`}>
                  {heroEstado === 'sin_mejora' ? 'ℹ️' : heroEstado === 'ahorro_bajo' ? 'ℹ️' : ''} {heroTitulo}
                </span>
                
                {heroEstado === 'ahorro_significativo' && (
                  <>
                    <div className="flex items-baseline justify-center gap-2 mb-4">
                      <h2 className="text-6xl font-black text-[#16A34A] tracking-tighter drop-shadow-sm">
                        {totalAnnualSaving.toFixed(0)}
                      </h2>
                      <span className="text-2xl font-bold text-[#16A34A]/80">€/año</span>
                    </div>
                    
                    <div className="inline-flex items-center gap-4 text-sm text-[#94A3B8] bg-[#020617]/50 rounded-full px-4 py-2 border border-white/5">
                      <div>
                        <span className="text-gray-500 mr-1">Actual:</span>
                        <span className="text-white font-mono line-through opacity-70">{currentTotalDisplay.toFixed(2)}€</span>
                      </div>
                      <div className="text-white">→</div>
                      <div>
                        <span className="text-gray-500 mr-1">Nueva:</span>
                        <span className="text-[#16A34A] font-bold font-mono">
                          {bestOffer && Number.isFinite(bestOffer.estimated_total) ? bestOffer.estimated_total.toFixed(2) : '---'}€
                        </span>
                        <span className="text-[10px] text-gray-500 ml-1">/mes</span>
                      </div>
                    </div>
                  </>
                )}

                {heroEstado === 'ahorro_bajo' && (
                  <>
                    <p className="text-gris-secundario mt-4 max-w-2xl mx-auto">
                      {heroMensaje}
                    </p>
                    <div className="mt-4 text-sm text-gris-secundario bg-white/5 inline-block px-4 py-2 rounded-lg">
                      <span>Ahorro potencial: </span>
                      <span className={heroColor}>{totalAnnualSaving.toFixed(0)}€/año</span>
                    </div>
                  </>
                )}

                {heroEstado === 'sin_mejora' && (
                  <>
                    <p className="text-gris-secundario mt-4 mb-6 max-w-2xl mx-auto">
                      {heroMensaje}
                    </p>
                    {showCTAs && (
                      <div className="flex flex-wrap justify-center gap-3 mt-6">
                        <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-gris-texto transition">
                          📅 Revisar en 3 meses
                        </button>
                        <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-gris-texto transition">
                          🔄 Simular cambio de hábitos
                        </button>
                        <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-gris-texto transition">
                          ⏰ Ver discriminación horaria
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Ofertas disponibles */}
              <div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {offers.map((offer, idx) => (
                    <OfferCard
                      key={offer.id ?? idx}
                      offer={offer}
                      isSelected={String(selectedOfferId) === String(offer.id)}
                      isRecommended={offer.tag === 'best_saving' && totalAnnualSaving >= UMBRAL_AHORRO_SIGNIFICATIVO}
                      isPartial={isPartialOffer(offer)}
                      onSelect={() => handleSelectOffer(offer)}
                    />
                  ))}
                </div>
              </div>

              {/* Footer de selección */}
              {selectedOffer && (
                <div className={`
                  border-2 rounded-xl p-6 transition-colors
                  ${isRecalculationNeeded 
                    ? 'bg-ambar-alerta/5 border-ambar-alerta/50' 
                    : 'bg-azul-control/10 border-azul-control'
                  }
                `}>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-azul-control text-lg">✓</span>
                      <h4 className="font-semibold text-gris-texto">
                        Oferta seleccionada: {selectedOffer.provider} - {selectedOffer.plan_name}
                      </h4>
                    </div>
                    <p className="text-gris-texto">
                      El cliente ahorrará <span className="font-bold text-verde-ahorro">
                        {(selectedOffer.saving_amount * 12).toFixed(0)}€ al año
                      </span>
                    </p>

                    <div className="mt-4 pt-4 border-t border-gris-secundario/20 flex items-center justify-between">
                      <button
                        onClick={() => setShowCommission(!showCommission)}
                        className="text-sm font-medium text-azul-control hover:text-blue-800 flex items-center gap-2 transition"
                      >
                        {showCommission ? '🔒 Ocultar comisión' : '👁️ Ver mi comisión'}
                      </button>
                      
                      {showCommission && (
                        <div className="bg-[#0B1220] px-3 py-1 rounded border border-white/10 shadow-sm">
                          <span className="text-xs text-gris-secundario mr-2">Tu comisión estimada:</span>
                          <span className="font-bold text-azul-control">{selectedOffer.commission.toFixed(2)}€</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </WizardLayout>

      {/* Modal de Éxito */}
      {showSuccessModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="bg-[#0F172A] border border-white/10 rounded-2xl p-8 max-w-md w-full shadow-2xl transform scale-100 transition-all">
            <div className="text-center">
              <div className="w-16 h-16 bg-verde-ahorro/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">🎉</span>
              </div>
              <h2 className="text-2xl font-bold text-gris-texto mb-2">
                ¡Presupuesto Generado!
              </h2>
              <p className="text-gris-secundario mb-6">
                El PDF se ha descargado correctamente. Revisa tu carpeta de descargas.
              </p>
              
              <div className="bg-white/5 p-4 rounded-xl mb-6 text-left">
                <p className="text-sm font-semibold text-gris-texto mb-1">Resumen:</p>
                <div className="flex justify-between text-sm">
                  <span>Ahorro anual:</span>
                  <span className="text-verde-ahorro font-bold">{(selectedOffer.saving_amount * 12).toFixed(0)}€</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Cliente:</span>
                  <span>{formData.cliente || '---'}</span>
                </div>
              </div>

              <div className="flex gap-3">
                <Button 
                  variant="secondary" 
                  className="flex-1"
                  onClick={() => setShowSuccessModal(false)}
                >
                  Cerrar
                </Button>
                <Link href="/dashboard" className="flex-1">
                  <Button variant="primary" className="w-full">
                    Ir al Dashboard
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
