export default function Input({
  id,
  name,
  type = 'text',
  value,
  onChange,
  placeholder,
  validated = false,
  error = false,
  errorMessage = '',
  className = '',
  ...props
}) {
  const stateClasses = validated 
    ? 'border-verde-ahorro bg-verde-ahorro/5' 
    : error 
    ? 'border-rojo-error bg-rojo-error/5' 
    : 'border-gris-secundario';

  return (
    <div className="w-full">
      <div className="relative">
        <input
          id={id}
          name={name}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={`w-full rounded-lg px-3 py-2 outline-none focus:border-azul-control focus:ring-2 focus:ring-azul-control/20 transition ${stateClasses} ${className}`}
          {...props}
        />
        {validated && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-verde-ahorro">
            ✓
          </span>
        )}
      </div>
      {error && errorMessage && (
        <p className="text-xs text-rojo-error mt-1">{errorMessage}</p>
      )}
    </div>
  );
}
