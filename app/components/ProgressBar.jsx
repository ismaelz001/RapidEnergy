export default function ProgressBar({ current, total, missingFields = [] }) {
  const percentage = (current / total) * 100;
  const isComplete = current === total;

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gris-texto font-medium">
          {current}/{total} campos completados
        </span>
        {missingFields.length > 0 && (
          <span className="text-xs text-ambar-alerta">
            Faltan: {missingFields.join(', ')}
          </span>
        )}
      </div>
      <div className="h-2 bg-gris-secundario/20 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${
            isComplete ? 'bg-verde-ahorro' : 'bg-ambar-alerta'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
