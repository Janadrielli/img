import { Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import Sidebar from './components/common/Sidebar';
import Dashboard from './components/dashboard/Dashboard';
import MapView from './components/map/MapView';
import DriversPanel from './components/drivers/DriversPanel';
import DeliveriesPanel from './components/deliveries/DeliveriesPanel';
import { useWebSocket } from './hooks/useWebSocket';
import { useStore } from './store/useStore';
import { api } from './services/api';

export default function App() {
  const { lastMessage, isConnected } = useWebSocket('dashboard-' + Date.now());
  const {
    setDrivers, setDeliveries, setRoutes, setStats, setIncidents,
    updateDriverLocation, updateDeliveryStatus, sidebarOpen,
  } = useStore();

  // Carregar dados iniciais
  useEffect(() => {
    const load = async () => {
      try {
        const [drivers, deliveries, routes, stats, incidents] = await Promise.all([
          api.getDrivers(),
          api.getDeliveries(),
          api.getRoutes(),
          api.getStats(),
          api.getIncidents(),
        ]);
        setDrivers(drivers);
        setDeliveries(deliveries);
        setRoutes(routes);
        setStats(stats);
        setIncidents(incidents);
      } catch (e) {
        console.error('Erro carregando dados:', e);
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [setDrivers, setDeliveries, setRoutes, setStats, setIncidents]);

  // Processar mensagens WebSocket
  useEffect(() => {
    if (!lastMessage) return;
    const { channel, data } = lastMessage;

    if (channel === 'driver:location' && data.driver_id) {
      updateDriverLocation(
        data.driver_id as string,
        data.lat as number,
        data.lng as number
      );
    }
    if (channel === 'delivery:update' && data.event === 'delivery_confirmed') {
      updateDeliveryStatus(data.delivery_id as string, 'confirmed');
    }
    if (channel === 'route:change') {
      api.getRoutes().then(setRoutes).catch(console.error);
    }
  }, [lastMessage, updateDriverLocation, updateDeliveryStatus, setRoutes]);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className={`flex-1 overflow-auto transition-all ${sidebarOpen ? 'ml-64' : 'ml-16'}`}>
        <header className="bg-white border-b px-6 py-3 flex items-center justify-between sticky top-0 z-10">
          <h1 className="text-xl font-bold text-gray-800">Fleet Route Optimizer</h1>
          <div className="flex items-center gap-3">
            <span className={`inline-flex items-center gap-1 text-sm ${isConnected ? 'text-green-600' : 'text-red-500'}`}>
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              {isConnected ? 'Tempo Real' : 'Desconectado'}
            </span>
          </div>
        </header>
        <div className="p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/map" element={<MapView />} />
            <Route path="/drivers" element={<DriversPanel />} />
            <Route path="/deliveries" element={<DeliveriesPanel />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
