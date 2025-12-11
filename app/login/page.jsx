export default function LoginPage() {
  return (
    <div className="flex flex-col items-center justify-center py-10">
      <div className="card w-full max-w-md">
        <h1 className="mb-4 text-xl font-semibold">Acceso</h1>
        <p className="mb-4 text-xs text-slate-300">
          Auth real vendrá más adelante. Por ahora esta pantalla sirve como placeholder
          visual para el futuro login de comerciales / administradores.
        </p>
        <form className="space-y-4">
          <div>
            <label className="label">Email</label>
            <input className="input" type="email" placeholder="tucorreo@empresa.com" />
          </div>
          <div>
            <label className="label">Contraseña</label>
            <input className="input" type="password" placeholder="********" />
          </div>
          <button type="button" className="btn-primary w-full">
            Entrar (falso por ahora)
          </button>
        </form>
      </div>
    </div>
  );
}
