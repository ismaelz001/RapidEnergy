"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';

// Usuarios de prueba (debe coincidir con CREDENCIALES_PRUEBA.md)
const USERS = {
  // DEV
  "ismael@rodorte.com": { password: "dev2026!", role: "dev", id: 1, name: "Ismael Rodríguez" },
  
  // CEOs
  "jose@asesoria.com": { password: "ceo2026!", role: "ceo", id: 2, name: "José Moreno" },
  "laura@energyplus.com": { password: "ceo2026!", role: "ceo", id: 6, name: "Laura Martínez" },
  "david@powerco.com": { password: "ceo2026!", role: "ceo", id: 9, name: "David Sánchez" },
  
  // COMERCIALES - Company 1 (Asesoría Energética)
  "ana@asesoria.com": { password: "comercial2026!", role: "comercial", id: 3, name: "Ana López" },
  "carlos@asesoria.com": { password: "comercial2026!", role: "comercial", id: 4, name: "Carlos Ruiz" },
  "juan@test.com": { password: "comercial2026!", role: "comercial", id: 5, name: "Juan Pérez" },
  
  // COMERCIALES - Company 2 (EnergyPlus)
  "pedro@energyplus.com": { password: "comercial2026!", role: "comercial", id: 7, name: "Pedro García" },
  "sofia@energyplus.com": { password: "comercial2026!", role: "comercial", id: 8, name: "Sofia Torres" },
  
  // COMERCIALES - Company 3 (PowerCo)
  "miguel@powerco.com": { password: "comercial2026!", role: "comercial", id: 10, name: "Miguel Ángel" },
  "elena@powerco.com": { password: "comercial2026!", role: "comercial", id: 11, name: "Elena Rodríguez" },
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    // Simular delay de red
    setTimeout(() => {
      const user = USERS[email];
      
      if (!user) {
        setError("Usuario no encontrado");
        setLoading(false);
        return;
      }
      
      if (user.password !== password) {
        setError("Contraseña incorrecta");
        setLoading(false);
        return;
      }

      // Guardar sesión en localStorage
      localStorage.setItem('user_id', user.id.toString());
      localStorage.setItem('user_role', user.role);
      localStorage.setItem('user_email', email);
      localStorage.setItem('user_name', user.name);
      
      // Redirigir según rol
      if (user.role === 'comercial') {
        router.push('/dashboard');
      } else {
        router.push('/gestion/resumen');
      }
      
      setLoading(false);
    }, 500);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] py-10">
      <div className="bg-[#0F172A] rounded-[16px] p-[32px] w-full max-w-md border border-white/8">
        <div className="mb-6">
          <h1 className="mb-2 text-2xl font-bold text-[#F1F5F9]">Iniciar Sesión</h1>
          <p className="text-sm text-[#94A3B8]">
            Accede al sistema CRM de MecaEnergy
          </p>
        </div>
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Email
            </label>
            <input 
              className="w-full px-4 py-3 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white placeholder-[#64748B] focus:outline-none focus:border-[#1E3A8A]" 
              type="email" 
              placeholder="usuario@empresa.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          
          <div>
            <label className="block text-sm font-semibold text-[#94A3B8] mb-2">
              Contraseña
            </label>
            <input 
              className="w-full px-4 py-3 bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white placeholder-[#64748B] focus:outline-none focus:border-[#1E3A8A]" 
              type="password" 
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          {error && (
            <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <button 
            type="submit" 
            className="w-full py-3 bg-[#1E3A8A] hover:bg-[#1E40AF] text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loading}
          >
            {loading ? 'Iniciando sesión...' : 'Entrar'}
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-[rgba(255,255,255,0.08)]">
          <p className="text-xs font-semibold text-[#94A3B8] mb-3">🔐 Usuarios de Prueba Disponibles:</p>
          
          <div className="space-y-3">
            {/* DEV */}
            <div className="bg-[rgba(255,255,255,0.03)] p-3 rounded-lg">
              <p className="text-xs font-semibold text-[#60A5FA] mb-2">👨‍💻 DESARROLLADOR</p>
              <div className="space-y-1 text-xs text-[#94A3B8]">
                <p>• ismael@rodorte.com / dev2026!</p>
              </div>
            </div>

            {/* CEOs */}
            <div className="bg-[rgba(255,255,255,0.03)] p-3 rounded-lg">
              <p className="text-xs font-semibold text-[#A78BFA] mb-2">👔 CEOs (3 Companies)</p>
              <div className="space-y-1 text-xs text-[#94A3B8]">
                <p>• jose@asesoria.com / ceo2026! <span className="text-[#64748B]">(Asesoría)</span></p>
                <p>• laura@energyplus.com / ceo2026! <span className="text-[#64748B]">(EnergyPlus)</span></p>
                <p>• david@powerco.com / ceo2026! <span className="text-[#64748B]">(PowerCo)</span></p>
              </div>
            </div>

            {/* COMERCIALES */}
            <div className="bg-[rgba(255,255,255,0.03)] p-3 rounded-lg">
              <p className="text-xs font-semibold text-[#34D399] mb-2">🤝 COMERCIALES (7 usuarios)</p>
              <div className="space-y-1 text-xs text-[#94A3B8]">
                <p className="text-[#64748B] font-medium">Company 1 - Asesoría:</p>
                <p>• ana@asesoria.com / comercial2026!</p>
                <p>• carlos@asesoria.com / comercial2026!</p>
                <p>• juan@test.com / comercial2026!</p>
                
                <p className="text-[#64748B] font-medium mt-2">Company 2 - EnergyPlus:</p>
                <p>• pedro@energyplus.com / comercial2026!</p>
                <p>• sofia@energyplus.com / comercial2026!</p>
                
                <p className="text-[#64748B] font-medium mt-2">Company 3 - PowerCo:</p>
                <p>• miguel@powerco.com / comercial2026!</p>
                <p>• elena@powerco.com / comercial2026!</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
