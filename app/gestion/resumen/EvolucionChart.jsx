"use client";

import { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function EvolucionChart() {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/api/stats/evolucion`, { cache: 'no-store' });
      
      if (!res.ok) {
        console.error('Error cargando evolución');
        setLoading(false);
        return;
      }

      const data = await res.json();
      
      // Preparar datos para Chart.js
      const labels = data.map(d => d.mes);
      const comisionesGeneradas = data.map(d => d.comisiones_generadas || 0);
      const comisionesPagadas = data.map(d => d.comisiones_pagadas || 0);

      setChartData({
        labels,
        datasets: [
          {
            label: 'Generadas',
            data: comisionesGeneradas,
            borderColor: '#0073EC',
            backgroundColor: 'rgba(0, 115, 236, 0.1)',
            fill: true,
            tension: 0.4,
          },
          {
            label: 'Pagadas',
            data: comisionesPagadas,
            borderColor: '#10B981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            fill: true,
            tension: 0.4,
          },
        ],
      });
    } catch (error) {
      console.error('[CHART] Error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0073EC]"></div>
      </div>
    );
  }

  if (!chartData) {
    return (
      <div className="text-center py-12 text-[#94A3B8]">
        No hay datos suficientes para mostrar gráfico
      </div>
    );
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: '#94A3B8',
          font: { size: 12 },
          usePointStyle: true,
        },
      },
      tooltip: {
        backgroundColor: '#1E293B',
        titleColor: '#fff',
        bodyColor: '#94A3B8',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        padding: 12,
        displayColors: true,
      },
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(255,255,255,0.05)',
        },
        ticks: {
          color: '#94A3B8',
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(255,255,255,0.05)',
        },
        ticks: {
          color: '#94A3B8',
          callback: (value) => `€${value}`,
        },
      },
    },
  };

  return (
    <div className="h-80">
      <Line data={chartData} options={options} />
    </div>
  );
}
