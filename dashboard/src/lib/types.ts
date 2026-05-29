/**
 * TypeScript types for TextSQL API
 * Matches the backend Pydantic schemas
 */

// Common Types
export interface ErrorResponse {
  error: string
  detail?: string
  code?: string
}

// Schema Types
export interface SchemaUploadRequest {
  name: string
  schema_format: 'sql_ddl' | 'prisma'
  db_type?: 'postgresql' | 'mysql'  // required for sql_ddl, optional for prisma
  sql_ddl: string  // SQL DDL text or raw .prisma file content
}

export interface Column {
  id: string
  name: string
  data_type: string
  is_nullable: boolean
  is_primary_key: boolean
  is_foreign_key: boolean
  foreign_key_table?: string | null
  foreign_key_column?: string | null
  enriched_description?: string | null
  description_source?: 'ai' | 'user' | null
}

export interface Table {
  id: string
  name: string
  enriched_description?: string | null
  description_source?: 'ai' | 'user' | null
  columns: Column[]
}

export interface Schema {
  id: string
  name: string
  db_type: string
  is_active: boolean
  created_at: string
  enriched_description?: string | null
  enriched_at?: string | null
  enrichment_status: 'pending' | 'running' | 'complete' | 'failed'
  enrichment_error?: string | null
  table_count: number
}

export interface SchemaDetail extends Schema {
  tables: Table[]
  raw_ddl_text?: string | null
  schema_format?: string | null  // 'sql_ddl' | 'prisma'
}

export interface SchemaListResponse {
  schemas: Schema[]
  total: number
}

// Query Types
export interface QueryRequest {
  schema_id: string
  query: string
}

export interface Query {
  id: string
  natural_language_query: string
  generated_sql: string
  confidence_score: number
  warnings: string[]
  ai_provider: string
  ai_model: string
  created_at: string
}

export interface QueryHistoryResponse {
  queries: Query[]
  total: number
}

export interface QueryFeedbackRequest {
  is_helpful: boolean
  is_correct: boolean
  feedback_notes?: string
}

// Integration Types
export interface CodeSnippet {
  code: string
  language: string
  language_name: string
  instructions: string
  file_extension: string
}

export interface SupportedLanguages {
  languages: Record<string, string>
}

// API Key Types
export interface APIKeyCreate {
  name?: string
  rate_limit_per_minute?: number
  rate_limit_per_hour?: number
  expires_at?: string  // ISO datetime string — computed from expires_in_days in the UI
}

export interface APIKeyResponse {
  id: string
  name: string | null
  is_active: boolean
  rate_limit_per_minute: number | null
  rate_limit_per_hour: number | null
  created_at: string
  expires_at: string | null
  last_used_at: string | null
}

export interface APIKeyCreateResponse {
  api_key: string
  key_info: APIKeyResponse
}

export interface APIKeyListResponse {
  keys: APIKeyResponse[]
  total: number
}

// User Authentication Types
export interface UserRegister {
  email: string
  password: string
  full_name?: string
  company_name: string
}

export interface UserLogin {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserResponse {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  is_email_verified: boolean
  is_admin: boolean
  company_id: string
  company_name: string
  created_at: string
  last_login_at: string | null
}

export interface AuthResponse {
  user: UserResponse
  tokens: TokenResponse
}

export interface UserUpdate {
  full_name?: string
  email?: string
}

export interface PasswordChange {
  current_password: string
  new_password: string
}

// API Response wrapper
export interface ApiResponse<T> {
  data?: T
  error?: ErrorResponse
}
