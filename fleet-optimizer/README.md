# Fleet Route Optimizer

Sistema de otimização de rotas para frotas logísticas com integração Waze em tempo real.

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FLEET ROUTE OPTIMIZER                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    WebSocket     ┌──────────────────────────────┐ │
│  │   Frontend   │◄───────────────►│         Backend              │ │
│  │   (React)    │    REST API      │       (FastAPI)              │ │
│  │              │◄───────────────►│                              │ │
│  └──────────────┘                  │  ┌────────────────────────┐ │ │
│                                    │  │   Route Optimizer      │ │ │
│  Features:                         │  │   Engine               │ │ │
│  • Mapa em tempo real              │  │   (Nearest-Neighbor +  │ │ │
│  • Painel de priorização           │  │    Waze Incidents)     │ │ │
│  • Tela de motoristas              │  └────────────────────────┘ │ │
│  • Drag & drop de entregas         │                              │ │
│  • Confirmação de recebimento      │  ┌────────────────────────┐ │ │
│                                    │  │   Waze Integration     │ │ │
│                                    │  │   Service              │ │ │
│                                    │  │   (Traffic + Alerts)   │ │ │
│                                    │  └────────────────────────┘ │ │
│                                    └──────────────────────────────┘ │
│                                                                      │
│  ┌──────────────┐                  ┌──────────────────────────────┐ │
│  │   Redis      │                  │   PostgreSQL                 │ │
│  │   (PubSub +  │                  │   (Dados persistentes)       │ │
│  │    Cache)    │                  │                              │ │
│  └──────────────┘                  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Stack Tecnológico

| Camada       | Tecnologia                                    |
|--------------|-----------------------------------------------|
| Backend      | Python 3.11 + FastAPI + SQLAlchemy + Alembic  |
| Real-time    | WebSocket (FastAPI) + Redis PubSub            |
| Frontend     | React 18 + TypeScript + Leaflet + TailwindCSS |
| Banco        | PostgreSQL 15 + PostGIS                       |
| Cache/PubSub | Redis 7                                       |
| Mapas        | Leaflet + OpenStreetMap + Waze Overlay        |
| Container    | Docker + Docker Compose                       |

## Funcionalidades Principais

1. **Otimização de Rotas em Tempo Real**
   - Nearest-neighbor com penalização por incidentes Waze
   - Re-roteamento automático após cada entrega confirmada
   - Consideração de janelas de tempo e prioridade

2. **Integração Waze**
   - Dados de tráfego em tempo real
   - Alertas de incidentes (acidentes, obras, polícia)
   - ETA atualizado continuamente

3. **Painel de Priorização**
   - Drag & drop para reordenar entregas
   - Classificação por urgência (Crítica, Alta, Normal, Baixa)
   - Gestor pode intervir e mudar rotas a qualquer momento

4. **Confirmação de Entrega**
   - Motorista confirma recebimento via app
   - Gatilho automático de re-otimização
   - Histórico de confirmações com timestamp e GPS

5. **Dashboard em Tempo Real**
   - Mapa com posição dos motoristas
   - Status de cada entrega
   - Alertas de atraso e incidentes

## Como Executar

```bash
# Com Docker Compose
docker-compose up -d

# Backend (desenvolvimento)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (desenvolvimento)
cd frontend
npm install
npm run dev
```

## Variáveis de Ambiente

```env
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/fleet_optimizer
REDIS_URL=redis://localhost:6379/0
WAZE_API_KEY=your_waze_api_key
WAZE_API_URL=https://www.waze.com/live-map/api

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

## Licença

Proprietário - Uso interno.
