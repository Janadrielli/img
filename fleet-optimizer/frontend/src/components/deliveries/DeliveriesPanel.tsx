/**
 * Painel de Priorização de Entregas com drag & drop.
 * Permite ao gestor reordenar entregas e mudar prioridades.
 */
import { useState, useCallback } from 'react';
import { useStore } from '../../store/useStore';
import { api } from '../../services/api';
import type { Delivery, DeliveryPriority } from '../../types';

const priorityConfig: Record<DeliveryPriority, { label: string; color: string; bg: string; score: number }> = {
  critical: { label: 'Crítica', color: 'text-red-700', bg: 'bg-red-100 border-red-300', score: 100 },
  high: { label: 'Alta', color: 'text-orange-700', bg: 'bg-orange-100 border-orange-300', score: 75 },
  normal: { label: 'Normal', color: 'text-blue-700', bg: 'bg-blue-100 border-blue-300', score: 50 },
  low: { label: 'Baixa', color: 'text-gray-700', bg: 'bg-gray-100 border-gray-300', score: 25 },
};

export default function DeliveriesPanel() {
  const { deliveries, routes, setDeliveries } = useStore();
  const [filter, setFilter] = useState<string>('all');
  const [savingOverride, setSavingOverride] = useState(false);
  const [draggedId, setDraggedId] = useState<string | null>(null);

  const filtered = deliveries.filter(d => {
    if (filter === 'all') return d.status !== 'cancelled';
    return d.status === filter;
  }).sort((a, b) => b.priority_score - a.priority_score);

  const handlePriorityChange = async (deliveryId: string, newPriority: DeliveryPriority) => {
    try {
      const score = priorityConfig[newPriority].score;
      await api.updateDelivery(deliveryId, { priority: newPriority, priority_score: score });
      setDeliveries(deliveries.map(d =>
        d.id === deliveryId ? { ...d, priority: newPriority, priority_score: score } : d
      ));
    } catch (e) {
      alert(`Erro: ${(e as Error).message}`);
    }
  };

  const handleDragStart = (id: string) => setDraggedId(id);
  const handleDragEnd = () => setDraggedId(null);

  const handleDrop = useCallback((targetId: string) => {
    if (!draggedId || draggedId === targetId) return;
    const items = [...filtered];
    const fromIdx = items.findIndex(d => d.id === draggedId);
    const toIdx = items.findIndex(d => d.id === targetId);
    if (fromIdx < 0 || toIdx < 0) return;

    const [moved] = items.splice(fromIdx, 1);
    items.splice(toIdx, 0, moved);

    // Atualizar scores baseado na nova posição
    const updated = items.map((d, idx) => ({
      ...d,
      priority_score: Math.max(100 - idx * 5, 1),
    }));
    setDeliveries(deliveries.map(d => {
      const upd = updated.find(u => u.id === d.id);
      return upd || d;
    }));
    setDraggedId(null);
  }, [draggedId, filtered, deliveries, setDeliveries]);

  const handleSaveOrder = async () => {
    if (!routes.length) return;
    setSavingOverride(true);
    try {
      const activeRoute = routes[0];
      const orderedIds = filtered
        .filter(d => d.status === 'assigned' || d.status === 'en_route')
        .map(d => d.id);
      await api.overridePriority(activeRoute.id, orderedIds, 'Reordenação manual pelo gestor');
      alert('Ordem salva com sucesso! Rota do motorista atualizada.');
    } catch (e) {
      alert(`Erro: ${(e as Error).message}`);
    } finally {
      setSavingOverride(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Priorização de Entregas</h2>
        <div className="flex gap-2">
          <button
            onClick={handleSaveOrder}
            disabled={savingOverride}
            className="px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {savingOverride ? 'Salvando...' : 'Salvar Ordem (Override)'}
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex gap-2 flex-wrap">
        {['all', 'pending', 'assigned', 'en_route', 'confirmed'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              filter === f ? 'bg-primary-600 text-white' : 'bg-white border text-gray-700 hover:bg-gray-50'
            }`}
          >
            {f === 'all' ? 'Todas' : f.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Info */}
      <p className="text-sm text-gray-500">
        Arraste as entregas para reordenar. Clique na prioridade para alterar. Total: {filtered.length}
      </p>

      {/* Lista de Entregas (drag & drop) */}
      <div className="space-y-2">
        {filtered.map((delivery, idx) => (
          <DeliveryRow
            key={delivery.id}
            delivery={delivery}
            index={idx}
            isDragging={draggedId === delivery.id}
            onDragStart={() => handleDragStart(delivery.id)}
            onDragEnd={handleDragEnd}
            onDrop={() => handleDrop(delivery.id)}
            onPriorityChange={handlePriorityChange}
          />
        ))}
      </div>
    </div>
  );
}


function DeliveryRow({
  delivery, index, isDragging, onDragStart, onDragEnd, onDrop, onPriorityChange,
}: {
  delivery: Delivery;
  index: number;
  isDragging: boolean;
  onDragStart: () => void;
  onDragEnd: () => void;
  onDrop: () => void;
  onPriorityChange: (id: string, p: DeliveryPriority) => void;
}) {
  const cfg = priorityConfig[delivery.priority];
  const [showPriorityMenu, setShowPriorityMenu] = useState(false);

  return (
    <div
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onDragOver={(e) => e.preventDefault()}
      onDrop={onDrop}
      className={`bg-white rounded-lg border p-3 flex items-center gap-3 cursor-grab active:cursor-grabbing transition-all ${
        isDragging ? 'opacity-50 ring-2 ring-primary-400' : 'hover:shadow-sm'
      }`}
    >
      {/* Grip */}
      <div className="text-gray-400 flex-shrink-0">
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path d="M7 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />
        </svg>
      </div>

      {/* Sequence */}
      <span className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center text-sm font-bold text-gray-700 flex-shrink-0">
        {index + 1}
      </span>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-gray-500">{delivery.order_number}</span>
          <span className="font-medium text-sm truncate">{delivery.customer_name}</span>
        </div>
        <p className="text-xs text-gray-500 truncate">{delivery.address}</p>
      </div>

      {/* Priority (clickable) */}
      <div className="relative">
        <button
          onClick={(e) => { e.stopPropagation(); setShowPriorityMenu(!showPriorityMenu); }}
          className={`px-2 py-0.5 rounded-full text-xs font-medium border ${cfg.bg} ${cfg.color}`}
        >
          {cfg.label}
        </button>
        {showPriorityMenu && (
          <div className="absolute right-0 top-full mt-1 bg-white border rounded-lg shadow-lg z-10 py-1 min-w-[100px]">
            {(Object.keys(priorityConfig) as DeliveryPriority[]).map(p => (
              <button
                key={p}
                onClick={(e) => {
                  e.stopPropagation();
                  onPriorityChange(delivery.id, p);
                  setShowPriorityMenu(false);
                }}
                className={`w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 ${priorityConfig[p].color}`}
              >
                {priorityConfig[p].label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Status */}
      <span className={`px-2 py-0.5 rounded text-xs flex-shrink-0 ${
        delivery.status === 'confirmed' ? 'bg-green-100 text-green-700' :
        delivery.status === 'en_route' ? 'bg-blue-100 text-blue-700' :
        'bg-gray-100 text-gray-600'
      }`}>
        {delivery.status}
      </span>

      {/* Time window */}
      {delivery.time_window_end && (
        <span className="text-xs text-gray-400 flex-shrink-0">
          {new Date(delivery.time_window_end).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
        </span>
      )}
    </div>
  );
}
