/**
 * Tela de Motoristas - Status, localização, demandas e rota atual.
 */
import { useState } from 'react';
import { useStore } from '../../store/useStore';
import { api } from '../../services/api';
import type { Driver } from '../../types';

const statusConfig: Record<string, { label: string; color: string; bg: string }> = {
  available: { label: 'Disponível', color: 'text-green-700', bg: 'bg-green-100' },
  en_route: { label: 'Em Rota', color: 'text-blue-700', bg: 'bg-blue-100' },
  delivering: { label: 'Entregando', color: 'text-purple-700', bg: 'bg-purple-100' },
  returning: { label: 'Retornando', color: 'text-orange-700', bg: 'bg-orange-100' },
  offline: { label: 'Offline', color: 'text-gray-700', bg: 'bg-gray-100' },
  break: { label: 'Pausa', color: 'text-yellow-700', bg: 'bg-yellow-100' },
};

export default function DriversPanel() {
  const { drivers, routes, deliveries, selectDriver, selectedDriverId } = useStore();
  const [optimizing, setOptimizing] = useState<string | null>(null);

  const handleOptimize = async (driverId: string) => {
    setOptimizing(driverId);
    try {
      await api.optimizeRoute(driverId);
      alert('Rota otimizada com sucesso!');
    } catch (e) {
      alert(`Erro: ${(e as Error).message}`);
    } finally {
      setOptimizing(null);
    }
  };

  const getDriverRoute = (driverId: string) =>
    routes.find(r => r.driver_id === driverId && (r.status === 'active' || r.status === 'planned'));

  const getDriverDeliveries = (driverId: string) => {
    const route = getDriverRoute(driverId);
    if (!route) return [];
    return route.stops
      .sort((a, b) => a.sequence_order - b.sequence_order)
      .map(stop => deliveries.find(d => d.id === stop.delivery_id))
      .filter(Boolean);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Motoristas ({drivers.length})</h2>
        <div className="flex gap-2 text-sm">
          {Object.entries(statusConfig).map(([key, cfg]) => {
            const count = drivers.filter(d => d.status === key).length;
            if (count === 0) return null;
            return (
              <span key={key} className={`px-2 py-0.5 rounded-full ${cfg.bg} ${cfg.color}`}>
                {cfg.label}: {count}
              </span>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {drivers.map((driver) => (
          <DriverCard
            key={driver.id}
            driver={driver}
            route={getDriverRoute(driver.id)}
            deliveryCount={getDriverDeliveries(driver.id).length}
            isSelected={selectedDriverId === driver.id}
            isOptimizing={optimizing === driver.id}
            onSelect={() => selectDriver(driver.id === selectedDriverId ? null : driver.id)}
            onOptimize={() => handleOptimize(driver.id)}
          />
        ))}
      </div>
    </div>
  );
}

function DriverCard({
  driver, route, deliveryCount, isSelected, isOptimizing, onSelect, onOptimize,
}: {
  driver: Driver;
  route: ReturnType<typeof Array.prototype.find>;
  deliveryCount: number;
  isSelected: boolean;
  isOptimizing: boolean;
  onSelect: () => void;
  onOptimize: () => void;
}) {
  const cfg = statusConfig[driver.status] || statusConfig.offline;

  return (
    <div
      className={`bg-white rounded-xl border p-4 transition-all cursor-pointer hover:shadow-md ${
        isSelected ? 'ring-2 ring-primary-500 shadow-md' : ''
      }`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">{driver.name}</h3>
          <p className="text-sm text-gray-500">{driver.vehicle_plate} - {driver.vehicle_type}</p>
        </div>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.color}`}>
          {cfg.label}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm mb-3">
        <div className="bg-gray-50 rounded p-2">
          <p className="text-gray-500 text-xs">Entregas</p>
          <p className="font-bold">{deliveryCount}/{driver.max_deliveries}</p>
        </div>
        <div className="bg-gray-50 rounded p-2">
          <p className="text-gray-500 text-xs">Localização</p>
          <p className="font-bold text-xs">
            {driver.current_lat ? `${driver.current_lat.toFixed(3)}, ${driver.current_lng?.toFixed(3)}` : 'N/A'}
          </p>
        </div>
      </div>

      {route && (
        <div className="bg-blue-50 rounded p-2 text-sm mb-3">
          <div className="flex justify-between">
            <span>Progresso: {(route as any).completed_stops}/{(route as any).total_stops}</span>
            <span>{(route as any).total_distance_km?.toFixed(1)} km</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-1.5 mt-1">
            <div
              className="bg-blue-600 h-1.5 rounded-full transition-all"
              style={{ width: `${((route as any).completed_stops / Math.max((route as any).total_stops, 1)) * 100}%` }}
            />
          </div>
        </div>
      )}

      <button
        onClick={(e) => { e.stopPropagation(); onOptimize(); }}
        disabled={isOptimizing || driver.status === 'offline'}
        className="w-full py-2 px-3 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isOptimizing ? 'Otimizando...' : 'Otimizar Rota'}
      </button>
    </div>
  );
}
