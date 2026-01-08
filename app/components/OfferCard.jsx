"use client";

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
      {/* Badge recomendado */}
      {isRecommended && (
        <div className="absolute -top-2 -right-2 bg-verde-ahorro text-white text-xs font-bold px-3 py-1 rounded-full">
          🏆 RECOMENDADO
        </div>
      )}

      {/* Proveedor y plan */}
      <div className="mb-4">
        <h4 className="text-lg font-bold text-gris-texto">{offer.provider}</h4>
        <p className="text-sm text-gris-secundario">{offer.plan_name}</p>
        {isPartial && (
          <>
            <p className="text-xs text-ambar-alerta mt-2 font-semibold">
              Estimacion parcial (sin potencia)
            </p>
            <p className="text-[11px] text-gris-secundario mt-1">
              Falta precio de potencia en la tarifa. No se puede comparar total correctamente.
            </p>
          </>
        )}
      </div>

      {/* Precio nuevo */}
      <div className="mb-4">
        <div className="text-3xl font-black text-azul-control">
          {offer.estimated_total?.toFixed(2)}€
        </div>
        <div className="text-xs text-gris-secundario">/mes</div>
      </div>

      {/* Divider */}
      <div className="border-t border-gris-secundario/20 my-4" />

      {/* Ahorro mensual */}
      <div className="mb-2">
        <div className="text-verde-ahorro font-semibold">
          -{offer.saving_amount?.toFixed(2)}€ ({offer.saving_percent}%)
        </div>
      </div>

      {/* Ahorro anual */}
      <div className="mb-4">
        <div className="text-xl font-bold text-verde-ahorro">
          {(offer.saving_amount * 12).toFixed(0)}€/año
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
