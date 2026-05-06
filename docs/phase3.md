# Nexus-Graph AI - Phase 3

## Real-Time Cognitive Dashboard & Knowledge Graph Interface

The Phase 3 frontend is a Next.js 14 App Router application in `frontend/`.

### Stack

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Shadcn-style local UI primitives
- React Flow
- Framer Motion
- Socket.io Client
- Zustand
- Recharts

### Routes

- `/` - enterprise cognitive dashboard
- `/graph` - interactive knowledge graph visualization
- `/timeline` - chronological reconstruction and replay mode
- `/conflicts` - real-time conflict intelligence
- `/decisions` - searchable decision lineage explorer

### Real-Time Streams

The frontend subscribes to:

- `decision:created`
- `conflict:detected`
- `graph:update`
- `timeline:update`
- `orchestration:status`

### Runtime

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3001`.

The UI hydrates from backend APIs when they are available and keeps demo-grade fallback state for judging flows.
