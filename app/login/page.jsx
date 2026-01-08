export default function LoginPage() {
  return (
    <div className="flex flex-col items-center justify-center py-10">
      <div className="bg-[#0F172A] rounded-[16px] p-[28px] w-full max-w-md border border-white/8">
        <h1 className="mb-4 text-xl font-semibold text-[#F1F5F9]">Acceso</h1>
        <p className="mb-4 text-xs text-[#94A3B8]">
          Auth real vendrá más adelante. Por ahora esta pantalla sirve como placeholder
          visual para el futuro login de comerciales / administradores.
        </p>
        <form className="space-y-4">
          <div>
            <label className="label text-[#F1F5F9]">Email</label>
            <input className="input" type="email" placeholder="tucorreo@empresa.com" />
          </div>
          <div>
            <label className="label text-[#F1F5F9]">Contraseña</label>
            <input className="input" type="password" placeholder="********" />
          </div>
          <button type="button" className="btn-primary w-full bg-[#1E3A8A] hover:bg-[#1E3A8A]/90 text-white font-semibold">
            Entrar (falso por ahora)
          </button>
        </form>
      </div>
    </div>
  );
}
