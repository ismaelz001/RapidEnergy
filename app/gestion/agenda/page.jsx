"use client";

import { useEffect, useState } from "react";
import { getTareasSemana, updateTarea, getAlertasRenovacion } from "@/lib/apiClient";

export default function AgendaSemanalPage() {
  const [tareas, setTareas] = useState([]);
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [semanaOffset, setSemanaOffset] = useState(0);
  const [filtroEstado, setFiltroEstado] = useState("todas"); // todas, pendiente, en_proceso

  useEffect(() => {
    fetchData();
  }, [semanaOffset]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [tareasData, alertasData] = await Promise.all([
        getTareasSemana(semanaOffset),
        getAlertasRenovacion({ estado: "pendiente", proximos_dias: 60 })
      ]);
      setTareas(tareasData.tareas || []);
      setAlertas(alertasData.alertas || []);
    } catch (error) {
      console.error("Error cargando datos:", error);
    }
    setLoading(false);
  };

  const handleCompletarTarea = async (tareaId) => {
    try {
      await updateTarea(tareaId, { estado: "completada" });
      fetchData();
    } catch (error) {
      console.error("Error completando tarea:", error);
      alert("Error al completar la tarea");
    }
  };

  // Agrupar tareas por día de la semana
  const tareasPorDia = tareas.reduce((acc, tarea) => {
    const dia = tarea.dia_semana; // 1=Lun, 7=Dom
    if (!acc[dia]) acc[dia] = [];
    acc[dia].push(tarea);
    return acc;
  }, {});

  const diasSemana = [
    { num: 1, nombre: "Lunes", abrev: "LUN" },
    { num: 2, nombre: "Martes", abrev: "MAR" },
    { num: 3, nombre: "Miércoles", abrev: "MIÉ" },
    { num: 4, nombre: "Jueves", abrev: "JUE" },
    { num: 5, nombre: "Viernes", abrev: "VIE" },
    { num: 6, nombre: "Sábado", abrev: "SÁB" },
    { num: 7, nombre: "Domingo", abrev: "DOM" }
  ];

  const alertasUrgentes = alertas.filter(a => a.es_urgente);

  const getPrioridadColor = (prioridad) => {
    switch (prioridad) {
      case "urgente": return "bg-red-100 text-red-800 border-red-300";
      case "alta": return "bg-orange-100 text-orange-800 border-orange-300";
      case "normal": return "bg-blue-100 text-blue-800 border-blue-300";
      case "baja": return "bg-gray-100 text-gray-800 border-gray-300";
      default: return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getPrioridadBadge = (prioridad) => {
    const colors = {
      urgente: "bg-red-500",
      alta: "bg-orange-500",
      normal: "bg-blue-500",
      baja: "bg-gray-400"
    };
    return colors[prioridad] || colors.normal;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-slate-800 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-7 gap-4">
              {[...Array(7)].map((_, i) => (
                <div key={i} className="h-64 bg-slate-800 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              📅 Agenda Semanal
            </h1>
            <p className="text-slate-400">
              Gestión de tareas y seguimiento de clientes
            </p>
          </div>

          {/* Alertas urgentes */}
          {alertasUrgentes.length > 0 && (
            <div className="mt-4 md:mt-0">
              <div className="bg-red-900/20 border border-red-700 rounded-lg px-4 py-2">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                  </span>
                  <span className="text-red-400 font-semibold">
                    {alertasUrgentes.length} renovación{alertasUrgentes.length > 1 ? "es" : ""} urgente{alertasUrgentes.length > 1 ? "s" : ""}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Controles de navegación */}
        <div className="flex items-center justify-between mb-6 bg-slate-900/50 rounded-xl p-4">
          <button
            onClick={() => setSemanaOffset(semanaOffset - 1)}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition"
          >
            ← Semana anterior
          </button>

          <span className="text-white font-semibold">
            {semanaOffset === 0 ? "Esta semana" : 
             semanaOffset === 1 ? "Próxima semana" :
             `Dentro de ${semanaOffset} semanas`}
          </span>

          <button
            onClick={() => setSemanaOffset(semanaOffset + 1)}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition"
          >
            Semana siguiente →
          </button>
        </div>

        {/* Grid de días */}
        <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
          {diasSemana.map((dia) => {
            const tareasDelDia = tareasPorDia[dia.num] || [];
            const tareasVisibles = filtroEstado === "todas" 
              ? tareasDelDia 
              : tareasDelDia.filter(t => t.estado === filtroEstado);

            return (
              <div
                key={dia.num}
                className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden"
              >
                {/* Header del día */}
                <div className="bg-gradient-to-r from-emerald-600 to-teal-600 p-4">
                  <div className="text-white font-bold text-sm">{dia.abrev}</div>
                  <div className="text-white/80 text-xs">{dia.nombre}</div>
                  {tareasDelDia.length > 0 && (
                    <div className="mt-2 bg-white/20 rounded-full px-2 py-1 text-xs text-white inline-block">
                      {tareasDelDia.length} tarea{tareasDelDia.length > 1 ? "s" : ""}
                    </div>
                  )}
                </div>

                {/* Lista de tareas */}
                <div className="p-3 space-y-3 min-h-[200px]">
                  {tareasVisibles.length === 0 ? (
                    <div className="text-slate-500 text-sm text-center py-8">
                      Sin tareas
                    </div>
                  ) : (
                    tareasVisibles.map((tarea) => (
                      <div
                        key={tarea.id}
                        className={`border rounded-lg p-3 transition hover:shadow-lg ${getPrioridadColor(tarea.prioridad)}`}
                      >
                        {/* Prioridad badge */}
                        <div className="flex items-start justify-between mb-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${getPrioridadBadge(tarea.prioridad)} text-white`}>
                            {tarea.prioridad.toUpperCase()}
                          </span>
                          <span className="text-xs text-slate-600">
                            #{tarea.id}
                          </span>
                        </div>

                        {/* Título */}
                        <h4 className="font-semibold text-sm mb-1 line-clamp-2">
                          {tarea.titulo}
                        </h4>

                        {/* Cliente */}
                        <p className="text-xs text-slate-600 mb-2">
                          Cliente: {tarea.cliente_nombre}
                        </p>

                        {/* Tipo */}
                        <div className="text-xs text-slate-500 mb-3">
                          {tarea.tipo.replace(/_/g, " ")}
                        </div>

                        {/* Botón completar */}
                        {tarea.estado === "pendiente" && (
                          <button
                            onClick={() => handleCompletarTarea(tarea.id)}
                            className="w-full text-xs bg-emerald-600 hover:bg-emerald-700 text-white py-2 rounded transition"
                          >
                            ✓ Completar
                          </button>
                        )}
                        {tarea.estado === "en_proceso" && (
                          <button
                            onClick={() => handleCompletarTarea(tarea.id)}
                            className="w-full text-xs bg-blue-600 hover:bg-blue-700 text-white py-2 rounded transition"
                          >
                            ✓ Finalizar
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Stats footer */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
            <div className="text-slate-400 text-sm">Total tareas</div>
            <div className="text-2xl font-bold text-white mt-1">{tareas.length}</div>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
            <div className="text-slate-400 text-sm">Pendientes</div>
            <div className="text-2xl font-bold text-orange-400 mt-1">
              {tareas.filter(t => t.estado === "pendiente").length}
            </div>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
            <div className="text-slate-400 text-sm">En proceso</div>
            <div className="text-2xl font-bold text-blue-400 mt-1">
              {tareas.filter(t => t.estado === "en_proceso").length}
            </div>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
            <div className="text-slate-400 text-sm">Alertas urgentes</div>
            <div className="text-2xl font-bold text-red-400 mt-1">
              {alertasUrgentes.length}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
