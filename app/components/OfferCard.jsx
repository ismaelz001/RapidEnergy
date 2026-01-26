"use client";

/**
 * OfferCard - Tarjeta de oferta con estados UX honestos (Nivel 2)
 * 
 * Reglas de umbrales (Ahorro Anual Normalizado):
 * - < 5€ => state="similar" (gris) "Condiciones similares a tu actual"
 * - 5€ a 30€ => state="optimizado" (gris) "Tu tarifa actual es competitiva"
 * - 30€ a 80€ => state="marginal" (azul) "Ahorro marginal detectado"
 * - >= 80€ => state="recomendado" (verde) "¡Ahorro claro detectado!"
 */

export const getUiState = (ahorroAnual) => {
  if (ahorroAnual < 5 && ahorroAnual >= -5) {
    return {
      state: 'similar',
      colorTexto: 'text-[#94A3B8]',
      mensaje: 'Condiciones similares a tu actual',
      icono: '≈',
      badgeColor: 'bg-gray-500',
      canBeRecommended: false
    };
  } else if (ahorroAnual >= 5 && ahorroAnual < 30) {
    return {
      state: 'optimizado',
      colorTexto: 'text-[#94A3B8]',
      mensaje: 'Tu tarifa actual es competitiva',
      icono: '↓',
      badgeColor: 'bg-gray-500',
      canBeRecommended: false
    };
  } else if (ahorroAnual >= 30 && ahorroAnual < 80) {
    return {
      state: 'marginal',
      colorTexto: 'text-[#3B82F6]',
      mensaje: 'Ahorro marginal detectado',
      icono: '↓',
      badgeColor: 'bg-[#3B82F6]',
      canBeRecommended: true
    };
  } else if (ahorroAnual >= 80) {
    return {
      state: 'recomendado',
      colorTexto: 'text-[#16A34A]',
      mensaje: '¡Ahorro claro detectado!',
      icono: '⬇',
      badgeColor: 'bg-[#16A34A]',
      canBeRecommended: true
    };
  } else {
    // Más costosa
    return {
      state: 'peor',
      colorTexto: 'text-[#F43F5E]',
      mensaje: 'Más costosa que tu tarifa actual',
      icono: '⬆',
      badgeColor: 'bg-red-500',
      canBeRecommended: false
    };
  }
};

export default function OfferCard({ 
  offer, 
  isSelected = false, 
  onSelect,
  isRecommended = false,
  isPartial = false
}) {
  const handleSelect = (event) => {
    if (isPartial) {
      event.preventDefault();
      return;
    }
    onSelect();
  };

  // Cifra reina: Ahorro anual normalizado (viene del backend)
  const ahorroAnual = offer.saving_amount_annual || 0;
  const ahorroMensual = offer.saving_amount_monthly || 0;
  const precioMensual = offer.estimated_total || 0;

  // Obtener estado UI
  const ui = getUiState(ahorroAnual);
  
  // Badge solo si es recomendado por sistema Y el ahorro >= 30€
  const showBadge = isRecommended && ui.canBeRecommended;

  return (
    <div
      className={`
        relative rounded-xl p-6 transition-all cursor-pointer h-full flex flex-col
        ${
          isSelected
            ? 'border-4 border-azul-control bg-azul-control/5 shadow-lg'
            : 'border border-white/5 bg-[#0F172A] hover:border-azul-control hover:shadow-xl'
        }
        ${isPartial ? 'opacity-80 cursor-not-allowed' : ''}
      `}
      onClick={handleSelect}
    >
      {/* Badge condicional */}
      {showBadge && (
        <div className={`absolute -top-2 -right-2 ${ui.badgeColor} text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg z-10 animate-fade-in`}>
          🏆 RECOMENDADO
        </div>
      )}

      {/* Proveedor y plan */}
      <div className="mb-4">
        <h4 className="text-lg font-bold text-gris-texto leading-tight">{offer.provider}</h4>
        <p className="text-sm text-gris-secundario">{offer.plan_name}</p>
        
        {isPartial && (
          <div className="mt-2 p-2 bg-ambar-alerta/10 rounded border border-ambar-alerta/20">
            <p className="text-[10px] text-ambar-alerta font-semibold uppercase tracking-wider">
              Estimación parcial
            </p>
            <p className="text-[10px] text-gris-secundario mt-0.5">
              Sin precios de potencia en tarifa.
            </p>
          </div>
        )}
      </div>

      {/* Precio mensual */}
      <div className="mb-4 mt-auto">
        <div className="text-3xl font-black text-azul-control">
          {precioMensual.toFixed(2)}€
        </div>
        <div className="text-xs text-gris-secundario">/mes (IVA incl.)</div>
      </div>

      {/* Divider */}
      <div className="border-t border-white/5 my-4" />

      {/* Mensaje de ahorro */}
      <div className="mt-auto">
        <div className={`font-semibold ${ui.colorTexto} flex items-center gap-1 text-sm mb-1`}>
          <span className="text-base">{ui.icono}</span>
          <span>{ui.mensaje}</span>
        </div>

        <div className={`text-xl font-bold ${ui.state === 'peor' ? 'text-gris-secundario opacity-60' : ui.colorTexto}`}>
          {ahorroAnual >= 0 ? '+' : ''}
          {ahorroAnual >= 5 || ahorroAnual <= -5 
            ? `${Math.abs(ahorroAnual).toFixed(0)}€/año`
            : `${Math.abs(ahorroMensual).toFixed(2)}€/mes`
          }
        </div>
      </div>

      {/* Botón de selección */}
      <div className="mt-6">
        <button
          className={`
            w-full py-2.5 rounded-lg font-bold transition-all text-sm
            ${
              isSelected
                ? 'bg-azul-control text-white shadow-md shadow-azul-control/20'
                : 'bg-white/5 border border-white/10 text-gris-texto hover:bg-white/10'
            }
            ${isPartial ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          onClick={(e) => {
            e.stopPropagation();
            handleSelect(e);
          }}
          disabled={isPartial}
        >
          {isPartial ? 'NO DISPONIBLE' : isSelected ? '✓ SELECCIONADA' : 'SELECCIONAR'}
        </button>
      </div>
    </div>
  );
}
