"use client";

import { createContext, useContext, useState, useEffect } from 'react';

const WizardContext = createContext();

export function WizardProvider({ children }) {
  // Estado del formulario (Paso 2)
  const [formData, setFormData] = useState({
    cups: 'ES0123456789012345AB',
    total_factura: '124.50',
    cliente: 'Juan López Martínez',
    consumo_total: '342', // Campo crítico
    iva: '26.14', // Campo crítico (si validado)
    // Otros valores por defecto para pruebas rápidas
    potencia_p1: '', potencia_p2: '', 
    consumo_p1: '', consumo_p2: '', consumo_p3: '', 
    consumo_p4: '', consumo_p5: '', consumo_p6: '',
    impuesto_electrico: '5.12'
  });

  // Estado de selección (Paso 3)
  const [selectedOfferId, setSelectedOfferId] = useState(null);
  
  // Firma de los datos al momento de seleccionar (para detectar cambios)
  const [selectionSignature, setSelectionSignature] = useState(null);

  // Función para calcular firma de datos críticos
  const calculateSignature = (data) => {
    // Campos que afectan el precio
    const criticalValues = [
      data.total_factura,
      data.consumo_total,
      data.potencia_p1,
      data.potencia_p2
    ];
    return JSON.stringify(criticalValues);
  };

  const updateFormData = (newData) => {
    setFormData(prev => ({ ...prev, ...newData }));
  };

  const selectOffer = (offerId) => {
    setSelectedOfferId(offerId);
    // Guardamos la "foto" de los datos actuales
    setSelectionSignature(calculateSignature(formData));
  };

  const checkRecalculationNeeded = () => {
    if (!selectedOfferId || !selectionSignature) return false;
    const currentSig = calculateSignature(formData);
    return currentSig !== selectionSignature;
  };

  return (
    <WizardContext.Provider value={{
      formData,
      updateFormData,
      selectedOfferId,
      selectOffer,
      checkRecalculationNeeded
    }}>
      {children}
    </WizardContext.Provider>
  );
}

export function useWizard() {
  return useContext(WizardContext);
}
