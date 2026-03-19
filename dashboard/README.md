# TextSQL Dashboard

A modern Next.js dashboard for the TextSQL API - Convert natural language to SQL with AI-powered generation.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm 9+
- TextSQL API running (backend)

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Configure your API URL in .env
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the dashboard.

## 📦 What's Included

### ✅ Completed Components

- **Next.js 14** with App Router and TypeScript
- **Tailwind CSS** for styling
- **API Client Library** (`src/lib/api-client.ts`) - Type-safe API calls
- **TypeScript Types** (`src/lib/types.ts`) - Full type definitions
- **Configuration Files** - All necessary config files
- **Landing Page** - Basic homepage
- **Development Setup** - Ready to build

### 🔨 To Be Implemented

The following pages and components need to be created:

#### Pages
- `src/app/dashboard/page.tsx` - Main dashboard
- `src/app/dashboard/schemas/page.tsx` - Schema list
- `src/app/dashboard/schemas/[id]/page.tsx` - Schema detail
- `src/app/dashboard/api-keys/page.tsx` - API key management
- `src/app/dashboard/queries/page.tsx` - Query history

#### Components
- `src/components/SchemaUpload.tsx` - Upload schema form
- `src/components/SchemaEditor.tsx` - Edit enriched descriptions
- `src/components/ApiKeyManager.tsx` - Manage API keys
- `src/components/QueryHistory.tsx` - Display query history
- `src/components/CodeSnippet.tsx` - Display code snippets
- `src/components/Layout/DashboardLayout.tsx` - Dashboard layout with sidebar

## 🛠️ Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **State Management:** Zustand (included)
- **Data Fetching:** SWR (included)
- **Notifications:** react-hot-toast
- **Icons:** lucide-react

## 📚 API Client Usage

The API client is fully implemented and ready to use:

```typescript
import { apiClient } from '@/lib/api-client'

// Set API key
apiClient.setApiKey('your-api-key')

// Upload schema
const schema = await apiClient.uploadSchema({
  name: 'My Database',
  connection_string: 'postgresql://...',
  include_sample_data: true
})

// Generate SQL
const query = await apiClient.generateSQL({
  schema_id: schema.id,
  query: 'Show all users created in the last 30 days'
})

// Get code snippet
const snippet = await apiClient.generateSnippet('python_flask', schema.id)
```

## 📖 Development Guide

### Project Structure

```
dashboard/
├── src/
│   ├── app/              # Next.js app router pages
│   │   ├── layout.tsx    # Root layout ✅
│   │   ├── page.tsx      # Landing page ✅
│   │   ├── globals.css   # Global styles ✅
│   │   └── dashboard/    # Dashboard pages (to implement)
│   ├── components/       # React components (to implement)
│   └── lib/              # Utilities and libraries
│       ├── api-client.ts # API client ✅
│       └── types.ts      # TypeScript types ✅
├── public/               # Static assets
└── package.json          # Dependencies ✅
```

### Environment Variables

Create a `.env` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_DEV_API_KEY=your-key-here (optional for development)
```

### Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm start            # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler check
```

## 🎨 Implementation Guide

See [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) for detailed step-by-step instructions on completing the dashboard.

## 🧪 Testing the API Client

The API client is ready to use. Test it in your components:

```typescript
'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import type { Schema } from '@/lib/types'

export default function SchemasPage() {
  const [schemas, setSchemas] = useState<Schema[]>([])

  useEffect(() => {
    async function loadSchemas() {
      const data = await apiClient.listSchemas()
      setSchemas(data.schemas)
    }
    loadSchemas()
  }, [])

  return (
    <div>
      {schemas.map(schema => (
        <div key={schema.id}>{schema.name}</div>
      ))}
    </div>
  )
}
```

## 📝 License

Proprietary - TextSQL Platform

## 🔗 Links

- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Dashboard:** http://localhost:3000

---

**Status:** Foundation Complete ✅ | Dashboard Pages: To Implement 🔨

See [Task_1.9_Completion_Summary.md](../docs/Task_1.9_Completion_Summary.md) for full details.
