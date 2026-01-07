export default function Badge({ children, variant = 'pendiente', className = '' }) {
  const variantClasses = {
    pendiente: "bg-ambar-alerta/10 text-ambar-alerta border-ambar-alerta",
    seleccionada: "bg-azul-control/10 text-azul-control border-azul-control",
    completada: "bg-verde-ahorro/10 text-verde-ahorro border-verde-ahorro"
  };

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border ${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  );
}
