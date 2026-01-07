export default function WizardStepper({ currentStep = 1 }) {
  const steps = [
    { number: 1, label: 'Factura' },
    { number: 2, label: 'Validar' },
    { number: 3, label: 'Comparar' }
  ];

  return (
    <div className="flex items-center justify-center gap-4 py-6">
      {steps.map((step, index) => (
        <div key={step.number} className="flex items-center">
          {/* Step circle */}
          <div className="flex flex-col items-center">
            <div
              className={`
                flex items-center justify-center w-10 h-10 rounded-full border-2 font-semibold text-sm
                ${
                  currentStep === step.number
                    ? 'bg-azul-control border-azul-control text-white'
                    : currentStep > step.number
                    ? 'bg-verde-ahorro border-verde-ahorro text-white'
                    : 'bg-white border-gris-secundario text-gris-secundario'
                }
              `}
            >
              {currentStep > step.number ? '✓' : step.number}
            </div>
            <span
              className={`
                mt-2 text-xs font-medium
                ${currentStep === step.number ? 'text-azul-control' : 'text-gris-secundario'}
              `}
            >
              {step.label}
            </span>
          </div>

          {/* Connector line */}
          {index < steps.length - 1 && (
            <div
              className={`
                w-24 h-0.5 mx-2
                ${currentStep > step.number ? 'bg-verde-ahorro' : 'bg-gris-secundario/30'}
              `}
            />
          )}
        </div>
      ))}
    </div>
  );
}
