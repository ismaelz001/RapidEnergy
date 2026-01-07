export default function Button({ 
  children, 
  variant = 'primary', 
  disabled = false, 
  onClick, 
  type = 'button',
  className = '' 
}) {
  const baseClasses = "inline-flex items-center justify-center rounded-lg px-6 py-3 font-semibold transition";
  
  const variantClasses = {
    primary: "bg-azul-control text-white hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed",
    secondary: "border border-gris-secundario text-gris-texto hover:bg-gris-fondo disabled:opacity-50 disabled:cursor-not-allowed"
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
    >
      {children}
    </button>
  );
}
