"use client";

import { useState, useEffect } from 'react';
import WizardLayout from '@/app/components/wizard/WizardLayout';
import OfferCard from '@/app/components/OfferCard';
import { useWizard } from '@/app/context/WizardContext';
import Button from '@/app/components/Button';
import { compareFactura } from '@/lib/apiClient';
import Link from 'next/link';

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

  // Verificar si hubo cambios en datatos críticos
  const isRecalculationNeeded = checkRecalculationNeeded();

  useEffect(() => {
    async function fetchOffers() {
      if (!params.id || params.id === 'new') {
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);
        const result = await compareFactura(params.id);
        // El backend devuelve { factura_id, current_total, offers: [...] }
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
        setError("No se pudieron generar ofertas para esta factura. Asegúrate de que los datos en el Paso 2 sean correctos.");
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
  
  // Encontrar el mejor ahorro para el hero
  const maxSaving = offers.length > 0 ? Math.max(...offers.map(o => o.saving_amount)) : 0;
  const bestOffer = offers.find(o => o.saving_amount === maxSaving);
  const totalAnnualSaving = bestOffer ? (bestOffer.saving_amount * 12).toFixed(0) : 0;

  const handleSelectOffer = (offer) => {
    selectOffer(offer.id);
  };

  const handleGeneratePresupuesto = () => {
    if (isRecalculationNeeded) return;
    setShowSuccessModal(true);
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

              {/* Hero de ahorro */}
              <div className="bg-verde-ahorro/10 border-2 border-verde-ahorro rounded-xl p-6">
                <h2 className="text-4xl font-black text-verde-ahorro mb-3">
                  ESTÁS AHORRANDO {totalAnnualSaving}€ AL AÑO
                </h2>
                <div className="text-gris-texto">
                  <span className="font-medium">Factura actual:</span> {currentTotalDisplay.toFixed(2)}€/mes
                  <span className="mx-2">→</span>
                  <span className="font-medium">Nueva factura:</span> {bestOffer && Number.isFinite(bestOffer.estimated_total) ? bestOffer.estimated_total.toFixed(2) : '---'}€/mes
                </div>
              </div>

              {/* Ofertas disponibles */}
              <div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {offers.map((offer, idx) => (
                    <OfferCard
                      key={offer.id ?? idx}
                      offer={offer}
                      isSelected={String(selectedOfferId) === String(offer.id)}
                      isRecommended={offer.tag === 'best_saving'}
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
                El PDF se ha descargado correctamente y se ha enviado una copia a tu email.
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
