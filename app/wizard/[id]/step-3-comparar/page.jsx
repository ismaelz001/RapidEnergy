"use client";

import { useState } from 'react';
import WizardLayout from '@/app/components/wizard/WizardLayout';
import OfferCard from '@/app/components/OfferCard';
import { useWizard } from '@/app/context/WizardContext';
import Button from '@/app/components/Button';

export default function Step3ComparerPage({ params }) {
  const { 
    formData, 
    selectedOfferId, 
    selectOffer, 
    checkRecalculationNeeded 
  } = useWizard();

  const [showCommission, setShowCommission] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  // Verificar si hubo cambios en datatos críticos
  const isRecalculationNeeded = checkRecalculationNeeded();

  // Mock data - simulación dinámica basada en formData
  const currentTotal = parseFloat(formData.total_factura || 0);
  
  // Si recalculamos, podríamos mostrar ofertas diferentes o "resetear" 
  // Por simplicidad, usamos las mismas pero simulamos que los valores dependen del total
  const offers = [
    {
      id: 1, // ID estable
      provider: "Endesa Energía XXI",
      plan_name: "Tarifa Plana 24h",
      estimated_total: currentTotal * 0.85,
      saving_amount: currentTotal * 0.15,
      saving_percent: 15,
      commission: (currentTotal * 0.15 * 12) * 0.03,
      tag: "best_saving"
    },
    {
      id: 2,
      provider: "Iberdrola One Luz",
      plan_name: "Plan Equilibrio",
      estimated_total: currentTotal * 0.88,
      saving_amount: currentTotal * 0.12,
      saving_percent: 12,
      commission: (currentTotal * 0.12 * 12) * 0.045,
      tag: "balanced"
    },
    {
      id: 3,
      provider: "Naturgy Gas y Luz",
      plan_name: "Más Ahorro Plus",
      estimated_total: currentTotal * 0.90,
      saving_amount: currentTotal * 0.10,
      saving_percent: 10,
      commission: (currentTotal * 0.10 * 12) * 0.06,
      tag: "best_commission"
    }
  ];

  const selectedOffer = selectedOfferId ? offers.find(o => o.id === selectedOfferId) : null;
  const maxSaving = Math.max(...offers.map(o => o.saving_amount));
  const bestOffer = offers.find(o => o.saving_amount === maxSaving);
  const totalAnnualSaving = bestOffer ? (bestOffer.saving_amount * 12).toFixed(0) : 0;

  const handleSelectOffer = (id) => {
    // Al seleccionar, se guarda la firma actual en el contexto
    selectOffer(id);
  };

  const handleGeneratePresupuesto = () => {
    if (isRecalculationNeeded) return;
    setShowSuccessModal(true);
  };

  const handleConfirmRecalculation = () => {
    // Al "reconfirmar", simplemente volvemos a seleccionar la misma oferta (actualizando la firma)
    // O pedimos al usuario que seleccione de nuevo. 
    // UX Spec dice: "deshabilita hasta reconfirmar". Una forma es obligar a clicar "Seleccionar" de nuevo.
    // Vamos a de-seleccionar para forzar elección consciente, o dar un botón de "Confirmar cambios".
    // Opción más segura: Forzar re-selección.
    selectOffer(null); 
  };

  return (
    <>
      <WizardLayout
        currentStep={3}
        nextLabel="GENERAR PRESUPUESTO"
        nextDisabled={!selectedOffer || isRecalculationNeeded}
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

          {/* Banner de Recálculo (Fix F5) */}
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
                className="bg-white border-ambar-alerta text-ambar-alerta hover:bg-ambar-alerta/5 whitespace-nowrap"
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
              <span className="font-medium">Factura actual:</span> {currentTotal.toFixed(2)}€/mes
              <span className="mx-2">→</span>
              <span className="font-medium">Nueva factura:</span> {bestOffer?.estimated_total.toFixed(2)}€/mes
            </div>
          </div>

          {/* Ofertas disponibles */}
          <div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {offers.map((offer) => (
                <OfferCard
                  key={offer.id}
                  offer={offer}
                  isSelected={selectedOfferId === offer.id}
                  isRecommended={offer.tag === 'best_saving'}
                  onSelect={() => handleSelectOffer(offer.id)}
                />
              ))}
            </div>
          </div>

          {/* Footer de selección (Fix F2) */}
          {selectedOffer && (
            <div className={`
              border-2 rounded-xl p-6 transition-colors
              ${isRecalculationNeeded 
                ? 'bg-ambar-alerta/5 border-ambar-alerta/50' // Visualmente "dirty"
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

                {/* Toggle de comisión y detalles */}
                <div className="mt-4 pt-4 border-t border-gris-secundario/20 flex items-center justify-between">
                  <button
                    onClick={() => setShowCommission(!showCommission)}
                    className="text-sm font-medium text-azul-control hover:text-blue-800 flex items-center gap-2 transition"
                  >
                    {showCommission ? '🔒 Ocultar comisión' : '👁️ Ver mi comisión'}
                  </button>
                  
                  {showCommission && (
                    <div className="bg-white px-3 py-1 rounded border border-gris-secundario shadow-sm">
                      <span className="text-xs text-gris-secundario mr-2">Tu comisión estimada:</span>
                      <span className="font-bold text-azul-control">{selectedOffer.commission.toFixed(2)}€</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </WizardLayout>

      {/* Modal de Éxito (Fix F3) */}
      {showSuccessModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl transform scale-100 transition-all">
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
              
              <div className="bg-gris-fondo p-4 rounded-xl mb-6 text-left">
                <p className="text-sm font-semibold text-gris-texto mb-1">Resumen:</p>
                <div className="flex justify-between text-sm">
                  <span>Ahorro anual:</span>
                  <span className="text-verde-ahorro font-bold">{(selectedOffer.saving_amount * 12).toFixed(0)}€</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Cliente:</span>
                  <span>{formData.cliente}</span>
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

import Link from 'next/link';
