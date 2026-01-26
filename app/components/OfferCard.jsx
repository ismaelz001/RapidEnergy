"use client";

/**
 * OfferCard - Tarjeta de oferta con estados UX honestos
 * 
 * Estados:
 * 1. Mejor significativo (ahorro >= 60€/año)
 * 2. Mejor mínimo (0 < ahorro < 60€/año)  
 * 3. Similar (-10€ <= ahorro <= 0€)
 * 4. Peor (ahorro < -10€)
 */

// Umbral de ahorro significativo (configurable)
const UMBRAL_AHORRO_SIGNIFICATIVO = 60; // €/año
const UMBRAL_SIMILAR = 10; // €/año de margen

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

  // Cálculos
  const ahorroMensual = offer.saving_amount || 0;
  const ahorroAnual = ahorroMensual * 12;
  const precioMensual = offer.estimated_total || 0;

  // Determinar estado UX
  let estado = 'similar';
  let colorTexto = 'text-[#64748B]'; // Gris neutral
  let colorFondo = 'bg-[#0F172A]';
  let mensaje = '';
  let icono = '≈';
  let showBadge = false;
  let badgeText = '';
  let badgeColor = '';

  if (ahorroAnual >= UMBRAL_AHORRO_SIGNIFICATIVO) {
    // Estado 1: Ahorro significativo
    estado = 'mejor_significativo';
    colorTexto = 'text-[#16A34A]';
    colorFondo = 'bg-[#0F172A]';
    mensaje = 'Más barata que tu tarifa actual';
    icono = '⬇';
    showBadge = isRecommended;
    badgeText = 'RECOMENDADO';
    badgeColor = 'bg-[#16A34A]';
  } else if (ahorroAnual > 0 && ahorroAnual < UMBRAL_AHORRO_SIGNIFICATIVO) {
    // Estado 2: Ahorro mínimo
    estado = 'mejor_minimo';
    colorTexto = 'text-[#3B82F6]';
    colorFondo = 'bg-[#0F172A]';
    mensaje = 'Ahorro mínimo detectado';
    icono = '↓';
    showBadge = false; //  No mostrar "RECOMENDADO" si ahorro es bajo
  } else if (ahorroAnual >= -UMBRAL_SIMILAR && ahorroAnual <= 0) {
    // Estado 3: Similar
    estado = 'similar';
    colorTexto = 'text-[#64748B]';
    colorFondo = 'bg-[#0F172A]';
    mensaje = `Similar a tu tarifa actual`;
    icono = '≈';
    showBadge = false;
  } else {
    // Estado 4: Peor
    estado = 'peor';
    colorTexto = 'text-[#94A3B8]';
    colorFondo = 'bg-[#0F172A]';
    mensaje = 'Más cara que tu tarifa';
    icono = '⬆';
    showBadge = false;
  }

  // Formatear diferencia para mostrar
  const diferenciaMostrar = Math.abs(ahorroAnual) < UMBRAL_SIMILAR 
    ? `${Math.abs(ahorroMensual).toFixed(2)}€/mes`
    : `${Math.abs(ahorroAnual).toFixed(0)}€/año`;

  return (
    <div
      className={`
        relative rounded-xl p-6 transition-all cursor-pointer
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
        <div className={`absolute -top-2 -right-2 ${badgeColor} text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg`}>
          🏆 {badgeText}
        </div>
      )}

      {/* Proveedor y plan */}
      <div className="mb-4">
        <h4 className="text-lg font-bold text-gris-texto">{offer.provider}</h4>
        <p className="text-sm text-gris-secundario">{offer.plan_name}</p>
        {isPartial && (
          <>
            <p className="text-xs text-ambar-alerta mt-2 font-semibold">
              Estimación parcial (sin potencia)
            </p>
            <p className="text-[11px] text-gris-secundario mt-1">
              Falta precio de potencia en la tarifa. No se puede comparar total correctamente.
            </p>
          </>
        )}
      </div>

      {/* Precio mensual (grande y claro) */}
      <div className="mb-4">
        <div className="text-3xl font-black text-azul-control">
          {precioMensual.toFixed(2)}€
        </div>
        <div className="text-xs text-gris-secundario">/mes</div>
      </div>

      {/* Divider */}
      <div className="border-t border-gris-secundario/20 my-4" />

      {/* Mensaje principal según estado */}
      <div className="mb-2">
        <div className={`font-semibold ${colorTexto} flex items-center gap-1`}>
          <span>{icono}</span>
          <span>{mensaje}</span>
        </div>
      </div>

      {/* Diferencia económica */}
      <div className="mb-4">
        <div className={`text-lg font-bold ${colorTexto}`}>
          {estado === 'peor' ? '+' : estado === 'similar' ? '±' : ''}
          {diferenciaMostrar}
        </div>
      </div>

      {/* Botón de selección */}
      <button
        className={`
          w-full py-2 rounded-lg font-semibold transition text-sm
          ${
            isSelected
              ? 'bg-azul-control text-white'
              : 'bg-transparent border border-white/10 text-[#F1F5F9] hover:bg-white/5'
          }
          ${isPartial ? 'opacity-50 cursor-not-allowed hover:bg-transparent' : ''}
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
  );
}
