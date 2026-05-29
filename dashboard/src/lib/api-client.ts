/**
 * TextSQL API Client
 * Provides type-safe methods for interacting with the TextSQL API
 */
import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  Schema,
  SchemaDetail,
  SchemaListResponse,
  SchemaUploadRequest,
  Query,
  QueryRequest,
  QueryHistoryResponse,
  QueryFeedbackRequest,
  CodeSnippet,
  SupportedLanguages,
  ErrorResponse,
  APIKeyCreate,
  APIKeyCreateResponse,
  APIKeyListResponse,
  UserRegister,
  UserLogin,
  AuthResponse,
  UserResponse,
  UserUpdate,
  PasswordChange,
} from './types'

export class TextSQLClient {
  private client: AxiosInstance
  private apiKey: string | null = null
  private accessToken: string | null = null

  constructor(baseURL?: string, apiKey?: string) {
    this.client = axios.create({
      baseURL: baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    })

    if (apiKey) {
      this.setApiKey(apiKey)
    }

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        if (error.response) {
          // Server responded with error
          throw new Error(
            error.response.data?.detail ||
            error.response.data?.error ||
            `API Error: ${error.response.status}`
          )
        } else if (error.request) {
          // No response received
          throw new Error('No response from server. Please check your connection.')
        } else {
          throw new Error(error.message)
        }
      }
    )
  }

  /**
   * Set API key for authentication
   */
  setApiKey(apiKey: string) {
    this.apiKey = apiKey
    this.client.defaults.headers.common['X-API-Key'] = apiKey
  }

  /**
   * Remove API key
   */
  clearApiKey() {
    this.apiKey = null
    delete this.client.defaults.headers.common['X-API-Key']
  }

  /**
   * Set JWT access token for authentication
   */
  setAccessToken(token: string) {
    this.accessToken = token
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  /**
   * Remove JWT access token
   */
  clearAccessToken() {
    this.accessToken = null
    delete this.client.defaults.headers.common['Authorization']
  }

  // ============================================================================
  // User Authentication Endpoints
  // ============================================================================

  /**
   * Register a new user and company
   */
  async register(data: UserRegister): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/v1/auth/register', data)
    return response.data
  }

  /**
   * Login with email and password
   */
  async login(data: UserLogin): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/v1/auth/login', data)
    return response.data
  }

  /**
   * Get current user information (requires JWT token)
   */
  async getCurrentUser(): Promise<UserResponse> {
    const response = await this.client.get<UserResponse>('/v1/auth/me')
    return response.data
  }

  /**
   * Update current user profile
   */
  async updateUserProfile(data: UserUpdate): Promise<UserResponse> {
    const response = await this.client.put<UserResponse>('/v1/auth/me', data)
    return response.data
  }

  /**
   * Change user password
   */
  async changePassword(data: PasswordChange): Promise<{ message: string; success: boolean }> {
    const response = await this.client.post('/v1/auth/change-password', data)
    return response.data
  }

  // ============================================================================
  // Schema Endpoints
  // ============================================================================

  /**
   * Upload and parse a database schema
   */
  async uploadSchema(data: SchemaUploadRequest): Promise<Schema> {
    const response = await this.client.post<Schema>('/v1/schemas', data)
    return response.data
  }

  /**
   * List all schemas
   */
  async listSchemas(activeOnly: boolean = true): Promise<SchemaListResponse> {
    const response = await this.client.get<SchemaListResponse>('/v1/schemas', {
      params: { active_only: activeOnly },
    })
    return response.data
  }

  /**
   * Get schema details by ID
   */
  async getSchema(schemaId: string): Promise<SchemaDetail> {
    const response = await this.client.get<SchemaDetail>(`/v1/schemas/${schemaId}`)
    return response.data
  }

  /**
   * Enrich schema with AI-generated descriptions
   */
  async enrichSchema(schemaId: string): Promise<Schema> {
    const response = await this.client.post<Schema>(`/v1/schemas/${schemaId}/enrich`)
    return response.data
  }

  /**
   * Update the schema-level enriched description (marks source as 'user')
   */
  async updateSchemaDescription(schemaId: string, description: string): Promise<Schema> {
    const response = await this.client.patch<Schema>(`/v1/schemas/${schemaId}`, {
      enriched_description: description,
    })
    return response.data
  }

  /**
   * Update a table's enriched description (marks source as 'user')
   */
  async updateTableDescription(
    schemaId: string,
    tableId: string,
    description: string
  ): Promise<import('./types').Table> {
    const response = await this.client.patch<import('./types').Table>(
      `/v1/schemas/${schemaId}/tables/${tableId}`,
      { enriched_description: description }
    )
    return response.data
  }

  /**
   * Update a column's enriched description (marks source as 'user')
   */
  async updateColumnDescription(
    schemaId: string,
    tableId: string,
    columnId: string,
    description: string
  ): Promise<import('./types').Column> {
    const response = await this.client.patch<import('./types').Column>(
      `/v1/schemas/${schemaId}/tables/${tableId}/columns/${columnId}`,
      { enriched_description: description }
    )
    return response.data
  }

  /**
   * Delete (deactivate) a schema
   */
  async deleteSchema(schemaId: string): Promise<void> {
    await this.client.delete(`/v1/schemas/${schemaId}`)
  }

  // ============================================================================
  // Query Endpoints
  // ============================================================================

  /**
   * Generate SQL from natural language
   */
  async generateSQL(data: QueryRequest): Promise<Query> {
    const response = await this.client.post<Query>('/v1/queries', data)
    return response.data
  }

  /**
   * Get query history
   */
  async getQueryHistory(schemaId?: string, limit: number = 50): Promise<QueryHistoryResponse> {
    const response = await this.client.get<QueryHistoryResponse>('/v1/queries', {
      params: {
        schema_id: schemaId,
        limit,
      },
    })
    return response.data
  }

  /**
   * Get specific query by ID
   */
  async getQuery(queryId: string): Promise<Query> {
    const response = await this.client.get<Query>(`/v1/queries/${queryId}`)
    return response.data
  }

  /**
   * Submit feedback for a query
   */
  async submitQueryFeedback(
    queryId: string,
    feedback: QueryFeedbackRequest
  ): Promise<{ query_id: string; feedback_recorded: boolean; message: string }> {
    const response = await this.client.post(`/v1/queries/${queryId}/feedback`, feedback)
    return response.data
  }

  // ============================================================================
  // Integration Endpoints
  // ============================================================================

  /**
   * Get supported languages for code snippets
   */
  async getSupportedLanguages(): Promise<SupportedLanguages> {
    const response = await this.client.get<SupportedLanguages>('/v1/integrations/languages')
    return response.data
  }

  /**
   * Generate code snippet for specific language
   */
  async generateSnippet(language: string, schemaId?: string): Promise<CodeSnippet> {
    const response = await this.client.post<CodeSnippet>('/v1/integrations/snippet', {
      language,
      schema_id: schemaId,
      base_url: this.client.defaults.baseURL,
    })
    return response.data
  }

  /**
   * Generate all code snippets
   */
  async generateAllSnippets(schemaId?: string): Promise<Record<string, CodeSnippet>> {
    const response = await this.client.get<{ snippets: Record<string, CodeSnippet> }>(
      '/v1/integrations/snippets',
      {
        params: {
          schema_id: schemaId,
          base_url: this.client.defaults.baseURL,
        },
      }
    )
    return response.data.snippets
  }

  // ============================================================================
  // API Key Management
  // ============================================================================

  /**
   * Create a new API key
   */
  async createApiKey(data: APIKeyCreate): Promise<APIKeyCreateResponse> {
    const response = await this.client.post<APIKeyCreateResponse>('/v1/auth/keys', data)
    return response.data
  }

  /**
   * List all API keys
   */
  async listApiKeys(includeInactive: boolean = false): Promise<APIKeyListResponse> {
    const response = await this.client.get<APIKeyListResponse>('/v1/auth/keys', {
      params: { include_inactive: includeInactive },
    })
    return response.data
  }

  /**
   * Revoke (deactivate) an API key
   */
  async revokeApiKey(keyId: string): Promise<void> {
    await this.client.delete(`/v1/auth/keys/${keyId}`)
  }

  /**
   * Get current authentication info
   */
  async getCurrentAuthInfo(): Promise<{
    company_id: string
    company_name: string
    is_active: boolean
    created_at: string
    authenticated: boolean
  }> {
    const response = await this.client.get('/v1/auth/me')
    return response.data
  }

  // ============================================================================
  // Visualization Endpoints
  // ============================================================================

  /**
   * Store query results and generate visualization
   */
  async displayResults(data: {
    query_id: string
    results: Array<Record<string, any>>
    generate_insight?: boolean
  }): Promise<{
    id: string
    query_id: string
    chart_type: string
    row_count: number
    column_count: number
    ai_insight: string | null
    visualization_data: any
    is_public: boolean
    created_at: string
    visualization_url: string
  }> {
    const response = await this.client.post('/v1/visualizations/display', data)
    return response.data
  }

  /**
   * Get visualization by ID (authenticated)
   */
  async getVisualization(resultId: string): Promise<{
    id: string
    query_id: string
    chart_type: string
    row_count: number
    column_count: number
    ai_insight: string | null
    visualization_data: any
    is_public: boolean
    created_at: string
    visualization_url: string
  }> {
    const response = await this.client.get(`/v1/visualizations/${resultId}`)
    return response.data
  }

  /**
   * Get public visualization by ID (no auth required)
   */
  async getPublicVisualization(resultId: string): Promise<{
    id: string
    query_id: string
    chart_type: string
    row_count: number
    column_count: number
    ai_insight: string | null
    visualization_data: any
    is_public: boolean
    created_at: string
    visualization_url: string
  }> {
    const response = await this.client.get(`/v1/visualizations/public/${resultId}`)
    return response.data
  }

  /**
   * List all visualizations for the company
   */
  async listVisualizations(
    queryId?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<{
    results: Array<{
      id: string
      query_id: string
      chart_type: string
      row_count: number
      ai_insight: string | null
      is_public: boolean
      created_at: string
    }>
    total: number
  }> {
    const response = await this.client.get('/v1/visualizations', {
      params: {
        query_id: queryId,
        limit,
        offset,
      },
    })
    return response.data
  }

  /**
   * Update visualization sharing settings
   */
  async updateVisualizationSharing(
    resultId: string,
    isPublic: boolean
  ): Promise<{
    id: string
    query_id: string
    chart_type: string
    row_count: number
    column_count: number
    ai_insight: string | null
    visualization_data: any
    is_public: boolean
    created_at: string
    visualization_url: string
  }> {
    const response = await this.client.patch(`/v1/visualizations/${resultId}/sharing`, {
      is_public: isPublic,
    })
    return response.data
  }

  /**
   * Delete a visualization
   */
  async deleteVisualization(resultId: string): Promise<void> {
    await this.client.delete(`/v1/visualizations/${resultId}`)
  }

  // ============================================================================
  // Health Check
  // ============================================================================

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    const response = await this.client.get('/health')
    return response.data
  }
}

// Export singleton instance
export const apiClient = new TextSQLClient()

// Export for creating custom instances
export default TextSQLClient
