# TextSQL - Ask Your Data. Get Answers.

A Text-to-SQL API and visualization platform that enables non-technical users to query databases using plain English.

## 🎯 Vision

Any company's employee can ask a question in plain English and get a beautiful, accurate answer from their own database — without writing a single line of SQL. TextSQL makes this possible, without ever touching the company's data.

## 🚀 Features

### Phase 1 (MVP) - Current
- ✅ Text-to-SQL conversion using AI
- ✅ Support for PostgreSQL and MySQL
- ✅ Schema upload and enrichment
- ✅ API-first architecture
- ✅ SQL security validation
- ✅ Rate limiting
- ✅ Query history

### Phase 2 (Coming Soon)
- 🔄 Automatic visualization generation
- 🔄 Role-based access control (RBAC)
- 🔄 SQL Server support

### Phase 3 (Planned)
- 📋 Enterprise features
- 📋 SSO integration
- 📋 Audit logging
- 📋 BigQuery & Snowflake support

## 🏗️ Architecture

```
┌─────────────────┐
│ Client App      │
│ (Your Backend)  │
└────────┬────────┘
         │ API Calls
         ▼
┌─────────────────┐
│ TextSQL API     │
│ (FastAPI)       │
├─────────────────┤
│ • SQL Generator │
│ • Schema Parser │
│ • Validator     │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────┐
│Postgres│ │Redis │
└────────┘ └──────┘
```

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (for local development)
- OpenAI API Key (for AI-powered SQL generation - required)
- Anthropic API Key (optional, for fallback)

## 🛠️ Installation

### Option 1: Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/textsql.git
cd textsql
```

2. Copy environment file:
```bash
cp backend/.env.example backend/.env
```

3. Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=your-key-here
```

4. Start services:
```bash
# Start only database and Redis
docker-compose up -d

# Or start everything including API
docker-compose --profile full up -d
```

5. Access the API:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Option 2: Local Development

1. Set up Python virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start PostgreSQL and Redis:
```bash
docker-compose up -d postgres redis
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the development server:
```bash
uvicorn app.main:app --reload
```

## 🧪 Running Tests

```bash
cd backend
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## 📚 API Documentation

### Quick Start

1. **Upload Your Schema**
```bash
curl -X POST http://localhost:8000/v1/schemas \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@schema.sql" \
  -F "database_type=postgresql" \
  -F "name=production_db"
```

2. **Generate SQL from Natural Language**
```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What were our top 5 products by revenue last month?",
    "schema_id": "your-schema-id",
    "role": "admin",
    "dialect": "postgresql"
  }'
```

3. **Execute SQL on Your Database**
```python
# In your backend
import psycopg2

# You run the SQL, not us
results = your_db.execute(generated_sql)
```

### Integration Examples

#### Python (Flask)
```python
import requests

# Step 1: Get SQL from TextSQL
response = requests.post(
    'http://localhost:8000/v1/query',
    headers={'Authorization': f'Bearer {API_KEY}'},
    json={
        'prompt': user_question,
        'schema_id': 'your-schema-id',
        'role': user.role
    }
)

sql = response.json()['sql']

# Step 2: Run on your database
data = db.execute(sql)

# Step 3: Return to user
return jsonify(data)
```

#### Node.js (Express)
```javascript
const axios = require('axios');

// Step 1: Get SQL
const result = await axios.post(
  'http://localhost:8000/v1/query',
  {
    prompt: question,
    schema_id: 'your-schema-id',
    role: user.role
  },
  {
    headers: { Authorization: `Bearer ${API_KEY}` }
  }
);

// Step 2: Run on your DB
const data = await db.query(result.data.sql);

// Step 3: Return
res.json(data);
```

## 🗂️ Project Structure

```
textsql/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core functionality (auth, config)
│   │   ├── db/           # Database connection
│   │   ├── models/       # SQLAlchemy models
│   │   ├── services/     # Business logic
│   │   ├── middleware/   # Custom middleware
│   │   └── prompts/      # AI prompts
│   ├── tests/            # Test files
│   ├── alembic/          # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard/            # Next.js dashboard (coming soon)
├── docs/                 # Documentation
├── docker-compose.yml
└── README.md
```

## 🔑 Security

### We NEVER Touch Your Data

- **Schema Only**: We only receive your database schema, never your data
- **No DB Access**: You execute SQL on your database, we never connect to it
- **Encrypted Storage**: All schemas encrypted at rest (AES-256)
- **API Key Auth**: Secure API key authentication
- **SQL Validation**: Automatic blocking of dangerous queries (DROP, DELETE, etc.)
- **Rate Limiting**: Prevent API abuse

### SQL Security

All generated SQL is validated to ensure:
- Only SELECT queries by default
- No DROP, DELETE, TRUNCATE, or other destructive operations
- No stored procedures or dynamic SQL execution
- Proper escaping and parameterization

## 📊 Database Schema

See [docs/database-schema.md](docs/database-schema.md) for complete schema documentation.

Key tables:
- `companies` - Multi-tenant root
- `api_keys` - API authentication
- `schemas` - Uploaded database schemas
- `schema_tables` - Table metadata
- `schema_columns` - Column metadata with descriptions
- `queries` - Query history and feedback
- `roles` - RBAC (Phase 2)

## 🛣️ Roadmap

### Month 1-3: MVP
- [x] FastAPI backend setup
- [x] Schema parser (PostgreSQL, MySQL)
- [x] SQL generator with AI
- [ ] API key management
- [ ] Rate limiting
- [ ] Basic dashboard
- [ ] Alpha testing

### Month 4-6: Visualization & Roles
- [ ] Automatic chart generation
- [ ] Role-based permissions
- [ ] SQL Server support
- [ ] Beta launch

### Month 7-10: Enterprise
- [ ] Write access (INSERT/UPDATE)
- [ ] SSO integration
- [ ] Audit logging
- [ ] SOC 2 compliance
- [ ] BigQuery & Snowflake support

See [docs/Phase_Implementation_Plan.md](docs/Phase_Implementation_Plan.md) for detailed roadmap.

## 🤝 Contributing

We're not accepting external contributions yet, but feel free to open issues for bugs or feature requests.

## 📝 License

Proprietary - All rights reserved

## 🆘 Support

- Documentation: [docs/](docs/)
- Email: support@textsql.com
- Issues: GitHub Issues

## 🙏 Acknowledgments

- Built with FastAPI, PostgreSQL, and OpenAI (with Anthropic support)
- Inspired by the need to democratize data access

---

**Made with ❤️ by the TextSQL Team**
