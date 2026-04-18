/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useCallback } from 'react';

const PredictionContext = createContext(null);

export function PredictionProvider({ children }) {
  const [predictions, setPredictions] = useState([]);

  const addPrediction = useCallback((pred) => {
    setPredictions((prev) => [pred, ...prev].slice(0, 500)); // keep last 500
  }, []);

  const stats = {
    total: predictions.length,
    attacks: predictions.filter((p) => p.prediction === 1).length,
    probes: predictions.filter((p) => p.prediction === 0).length,
    highSeverity: predictions.filter((p) => p.severity === 'HIGH').length,
    lastUpdated: predictions[0]?.timestamp || null,
  };

  return (
    <PredictionContext.Provider value={{ predictions, addPrediction, stats }}>
      {children}
    </PredictionContext.Provider>
  );
}

export function usePredictions() {
  const ctx = useContext(PredictionContext);
  if (!ctx) throw new Error('usePredictions must be used inside PredictionProvider');
  return ctx;
}
