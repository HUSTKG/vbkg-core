// API Helpers
export const API_ENDPOINTS = {
  LOGIN: "/auth/login",
  LOGIN_JSON: "/auth/login/json",
  REGISTER: "/auth/register",
  LOGOUT: "/auth/logout",

  // Data Sources
  CREATE_DATASOURCE: "/datasources",
  READ_DATASOURCES: "/datasources",
  READ_DATASOURCE: (id: string) => `/datasources/${id}`,
  UPDATE_DATASOURCE: (id: string) => `/datasources/${id}`,
  DELETE_DATASOURCE: (id: string) => `/datasources/${id}`,
  GET_PIPELINE_TEMPLATES: (datasource_id: string) =>
    `/datasources/${datasource_id}/pipeline-templates`,
  CREATE_PIPELINE_FROM_TEMPLATE: (datasource_id: string) =>
    `/datasources/${datasource_id}/create-pipeline`,

  // File Upload
  UPLOAD_FILE: "/upload",
  READ_FILE_UPLOADS: "/upload/files",
  READ_FILE_UPLOAD: (id: string) => `/upload/files/${id}`,
  UPDATE_FILE_STATUS: (file_id: string) => `/upload/files/${file_id}/status`,
  DELETE_FILE_UPLOAD: (file_id: string) => `/upload/files/${file_id}`,
  READ_FILE_CONTENT: (file_id: string) => `/upload/files/${file_id}/content`,
  GET_FILE_PUBLIC_URL: (file_id: string) => `/upload/files/${file_id}/public`,
  UPDATE_FILE_METADATA: (file_id: string) =>
    `/upload/files/${file_id}/metadata`,

  // Fibo
  READ_FIBO_CLASSES: "/fibo/classes",
  READ_FIBO_CLASS: (id: string) => `/fibo/classes/${id}`,
  CREATE_FIBO_CLASS: "/fibo/classes",
  UPDATE_FIBO_CLASS: (id: string) => `/fibo/classes/${id}`,
  DELETE_FIBO_CLASS: (id: string) => `/fibo/classes/${id}`,
  READ_FIBO_PROPERTIES: "/fibo/properties",
  READ_FIBO_PROPERTY: (id: string) => `/fibo/properties/${id}`,
  CREATE_FIBO_PROPERTY: "/fibo/properties",
  UPDATE_FIBO_PROPERTY: (id: string) => `/fibo/properties/${id}`,
  DELETE_FIBO_PROPERTY: (id: string) => `/fibo/properties/${id}`,
  IMPORT_ONTOLOGY: "/fibo/import",
  READ_ENTITY_MAPPINGS: "/fibo/entity-mappings",
  CREATE_ENTITY_MAPPING: "/fibo/entity-mappings",
  DELETE_ENTITY_MAPPING: (id: string) => `/fibo/entity-mappings/${id}`,
  VERIFY_ENTITY_MAPPING: (id: string) => `/fibo/entity-mappings/${id}/verify`,
  READ_RELATIONSHIP_MAPPINGS: "/fibo/relationship-mappings",
  CREATE_RELATIONSHIP_MAPPING: "/fibo/relationship-mappings",
  DELETE_RELATIONSHIP_MAPPING: (id: string) =>
    `/fibo/relationship-mappings/${id}`,
  VERIFY_RELATIONSHIP_MAPPING: (id: string) =>
    `/fibo/relationship-mappings/${id}/verify`,
  SUGGEST_FIBO_CLASSES: "/fibo/suggest/classes",
  SUGGEST_FIBO_PROPERTIES: "/fibo/suggest/properties",

  // Knowledge Graph - NEW ENDPOINTS
  // Entities
  GET_KG_ENTITY: (entity_id: string) =>
    `/knowledge-graph/entities/${entity_id}`,
  SEARCH_KG_ENTITIES: "/knowledge-graph/entities",
  GET_KG_ENTITY_TYPES: "/knowledge-graph/entities/types",
  GET_KG_ENTITY_NEIGHBORS: (entity_id: string) =>
    `/knowledge-graph/entities/${entity_id}/neighbors`,

  // Relationships
  SEARCH_KG_RELATIONSHIPS: "/knowledge-graph/relationships",
  GET_KG_RELATIONSHIP: (relationship_id: string) =>
    `/knowledge-graph/relationships/${relationship_id}`,
  GET_KG_ENTITY_RELATIONSHIPS: (entity_id: string) =>
    `/knowledge-graph/entities/${entity_id}/relationships`,

  // Graph Traversal
  GET_KG_SUBGRAPH: (entity_id: string) =>
    `/knowledge-graph/entities/${entity_id}/subgraph`,
  FIND_KG_PATHS: "/knowledge-graph/paths",
  EXECUTE_KG_QUERY: "/knowledge-graph/query",

  // Analytics & Statistics
  GET_KG_STATS: "/knowledge-graph/stats",
  GET_KG_INVESTMENT_INSIGHTS: "/knowledge-graph/insights/investment",

  // Search & Discovery
  KG_GLOBAL_SEARCH: "/knowledge-graph/search",

  // Knowledge
  CREATE_ENTITY: "/knowledge-graph/entities",
  UPDATE_ENTITY: (id: string) => `/knowledge-graph/entities/${id}`,
  DELETE_ENTITY: (id: string) => `/knowledge-graph/entities/${id}`,
  CREATE_RELATIONSHIP: "/knowledge-graph/relationships",
  EXCUTE_QUERY: "/knowledge-graph/query",
  GET_KNOWLEDGE_GRAPH_STATS: "/knowledge-graph/graph/stats",
  CREATE_OR_MERGE_ENTITY: "/knowledge-graph/entities/merge",

  // Notifications
  READ_NOTIFICATIONS: "/notifications",
  READ_NOTIFICATION: (id: string) => `/notifications/${id}`,
  CREATE_NOTIFICATION: "/notifications",
  MARK_NOTIFICATION_READ: (id: string) => `/notifications/${id}/read`,
  UPDATE_NOTIFICATION: (id: string) => `/notifications/${id}`,
  DELETE_NOTIFICATION: (id: string) => `/notifications/${id}`,

  // Pipelines
  READ_PIPELINES: "/pipelines",
  CREATE_PIPELINE: "/pipelines",
  READ_PIPELINE: (id: string) => `/pipelines/${id}`,
  UPDATE_PIPELINE: (id: string) => `/pipelines/${id}`,
  DELETE_PIPELINE: (id: string) => `/pipelines/${id}`,
  RUN_PIPELINE: (id: string) => `/pipelines/${id}/run`,
  READ_PIPELINE_RUNS: (pipeline_id: string) => `/pipelines/${pipeline_id}/runs`,
  READ_PIPELINE_RUN: (run_id: string) => `/pipelines/runs/${run_id}`,
  GET_PIPELINE_RUN_STATUS: (run_id: string) =>
    `/pipelines/runs/${run_id}/status`,
  CANCEL_PIPELINE_RUN: (run_id: string) => `/pipelines/runs/${run_id}/cancel`,
  READ_PIPELINE_STEP: (step_id: string, pipeline_id: string) =>
    `/pipelines/${pipeline_id}/steps/${step_id}`,
  READ_PIPELINE_STEPS: (pipeline_id: string) =>
    `/pipelines/${pipeline_id}/steps`,
  READ_PIPELINE_STEP_RUNS: (pipeline_run_id: string) =>
    `/pipelines/runs/${pipeline_run_id}/steps`,
  READ_PIPELINE_STEP_RUN: (step_run_id: string, pipeline_run_id: string) =>
    `/pipelines/runs/${pipeline_run_id}/steps/${step_run_id}`,

  // Search
  SEARCH_ENTITIES: "/search/entities",
  FIND_SIMILAR_ENTITIES: "/search/similar",
  GRAPH_SEARCH: "/search/graph",
  GENERATE_EMBEDDINGS: "/search/embeddings",
  CREATE_ENTITY_EMBEDDING: (entity_id: string) =>
    `/search/entities/${entity_id}/embedding`,
  UPDATE_ENTITY_EMBEDDINGS_BATCH: "/search/entities/embeddings/batch",

  // Enhanced User Management
  READ_USERS: "/users",
  READ_USER_ME: "/users/me",
  UPDATE_USER_ME: "/users/me",
  READ_USER: (id: string) => `/users/${id}`,
  UPDATE_USER: (id: string) => `/users/${id}`,
  DELETE_USER: (id: string) => `/users/${id}`,

  // Role & Permission Management
  READ_ROLES: "/users/roles",
  READ_PERMISSIONS: "/users/permissions",
  ASSIGN_USER_ROLE: (user_id: string, role_name: string) =>
    `/users/${user_id}/roles/${role_name}`,
  REMOVE_USER_ROLE: (user_id: string, role_name: string) =>
    `/users/${user_id}/roles/${role_name}`,

  // API Key Management
  CREATE_API_KEY: "/users/api-keys",
  READ_USER_API_KEYS: "/users/api-keys",
  REVOKE_API_KEY: (api_key_id: string) => `/users/api-keys/${api_key_id}`,

  // User Activity & Monitoring
  READ_MY_ACTIVITY: "/users/me/activity",
  READ_USER_ACTIVITY: (user_id: string) => `/users/${user_id}/activity`,

  // Admin Dashboard
  ADMIN_SYSTEM_STATS: "/users/admin/stats",

  // Visualizations
  CREATE_VISUALIZATION: "/visualizations",
  READ_VISUALIZATIONS: "/visualizations",
  READ_PUBLIC_VISUALIZATIONS: "/visualizations/public",
  READ_VISUALIZATION: (id: string) => `/visualizations/${id}`,
  UPDATE_VISUALIZATION: (id: string) => `/visualizations/${id}`,
  DELETE_VISUALIZATION: (id: string) => `/visualizations/${id}`,
  GET_VISUALIZATION_DATA: (id: string) => `/visualizations/${id}/data`,
  CREATE_DEFAULT_VISUALIZATION: "/visualizations/default",
  GET_VISUALIZATION_TEMPLATES: "/visualizations/template",

  // Upload
  INIT_UPLOAD_FILE: "/upload",

  // Quality Management
  QUALITY_DASHBOARD: "/quality/dashboard",
  QUALITY_REPORT: "/quality/report",
  QUALITY_MONITORING_RUN: "/quality/monitoring/run", // POST - run monitoring

  // Conflicts Management
  GET_CONFLICTS: "/quality/conflicts",
  DETECT_CONFLICTS: "/quality/conflicts/detect",
  RESOLVE_CONFLICT: (conflict_id: string) =>
    `/quality/conflicts/${conflict_id}/resolve`,
  AUTO_RESOLVE_CONFLICT: (conflict_id: string) =>
    `/quality/conflicts/${conflict_id}/auto-resolve`,

  // KG Editing
  APPLY_KG_EDIT: "/quality/kg/edit",
  ROLLBACK_KG_CHANGES: "/quality/kg/rollback",
  ADD_QUALITY_STEPS_TO_PIPELINE: (pipeline_id: string) =>
    `/quality/pipeline/${pipeline_id}/add-quality-steps`,

  // Validation Rules Management
  VALIDATION_RULES: "/validation/rules",
  VALIDATION_RULE: (rule_id: string) => `/validation/rules/${rule_id}`,
  VALIDATION_RULE_TOGGLE: (rule_id: string) =>
    `/validation/rules/${rule_id}/toggle`,
  VALIDATION_RULE_EXECUTE: (rule_id: string) =>
    `/validation/rules/${rule_id}/execute`,
  VALIDATION_RULES_EXECUTE_BATCH: "/validation/rules/execute-batch",

  // Rule Executions
  VALIDATION_EXECUTIONS: "/validation/executions",
  VALIDATION_EXECUTION: (execution_id: string) =>
    `/validation/executions/${execution_id}`,

  // Violations Management
  VALIDATION_VIOLATIONS: "/validation/violations",
  VALIDATION_VIOLATION: (violation_id: string) =>
    `/validation/violations/${violation_id}`,
  VALIDATION_VIOLATIONS_BULK_UPDATE: "/validation/violations/bulk-update",

  // Statistics & Performance
  VALIDATION_DASHBOARD: "/validation/dashboard",
  VALIDATION_PERFORMANCE: "/validation/performance",
  VALIDATION_SUMMARY: "/validation/summary",

  // Rule Templates
  VALIDATION_TEMPLATES: "/validation/templates",
  VALIDATION_TEMPLATE_CREATE_RULE: (template_id: string) =>
    `/validation/templates/${template_id}/create-rule`,

  // Pipeline Integration
  VALIDATION_ADD_TO_PIPELINE: (pipeline_id: string) =>
    `/validation/pipeline/${pipeline_id}/add-validation-step`,

  // === Domain Management - NEW ENDPOINTS ===
  // Domains
  CREATE_DOMAIN: "/domain/domains",
  READ_DOMAINS: "/domain/domains",
  READ_DOMAIN: (id: string) => `/domain/domains/${id}`,
  UPDATE_DOMAIN: (id: string) => `/domain/domains/${id}`,
  DELETE_DOMAIN: (id: string) => `/domain/domains/${id}`,
  GET_DOMAIN_STATS: (id: string) => `/domain/domains/${id}/stats`,

  // Entity Types
  CREATE_ENTITY_TYPE: "/domain/entity-types",
  READ_ENTITY_TYPES: "/domain/entity-types",
  READ_ENTITY_TYPE: (id: string) => `/domain/entity-types/${id}`,
  UPDATE_ENTITY_TYPE: (id: string) => `/domain/entity-types/${id}`,
  DELETE_ENTITY_TYPE: (id: string) => `/domain/entity-types/${id}`,

  // Relationship Types
  CREATE_RELATIONSHIP_TYPE: "/domain/relationship-types",
  READ_RELATIONSHIP_TYPES: "/domain/relationship-types",
  READ_RELATIONSHIP_TYPE: (id: string) => `/domain/relationship-types/${id}`,
  UPDATE_RELATIONSHIP_TYPE: (id: string) => `/domain/relationship-types/${id}`,
  DELETE_RELATIONSHIP_TYPE: (id: string) => `/domain/relationship-types/${id}`,

  // Domain Mappings
  ADD_ENTITY_TYPE_TO_DOMAIN: (type_id: string) =>
    `/domain/entity-types/${type_id}/domains`,
  REMOVE_ENTITY_TYPE_FROM_DOMAIN: (type_id: string, domain_id: string) =>
    `/domain/entity-types/${type_id}/domains/${domain_id}`,
  ADD_RELATIONSHIP_TYPE_TO_DOMAIN: (type_id: string) =>
    `/domain/relationship-types/${type_id}/domains`,
  REMOVE_RELATIONSHIP_TYPE_FROM_DOMAIN: (type_id: string, domain_id: string) =>
    `/domain/relationship-types/${type_id}/domains/${domain_id}`,

  // Validation
  VALIDATE_TYPE_CONSTRAINTS: "/domain/validate",

  // Utility Endpoints
  GET_ENTITY_TYPES_BY_DOMAIN: (domain_name: string) =>
    `/domain/entity-types/by-domain/${domain_name}`,
  GET_RELATIONSHIP_TYPES_BY_DOMAIN: (domain_name: string) =>
    `/domain/relationship-types/by-domain/${domain_name}`,
  GET_COMPATIBLE_RELATIONSHIPS: "/domain/compatible-relationships",

  // Celery & Flower Monitoring
  CELERY_DASHBOARD: "/celery/dashboard",
  CELERY_WORKERS: "/celery/workers",
  CELERY_WORKER_STATS: "/celery/workers/stats",
  CELERY_TASKS: "/celery/tasks",
  CELERY_STATS: "/celery/stats",
  CELERY_HEALTH: "/celery/health",
  CELERY_WORKER_DETAIL: (worker_name: string) =>
    `/celery/workers/${encodeURIComponent(worker_name)}`,
  CELERY_TASK_DETAIL: (task_id: string) => `/celery/tasks/${task_id}`,
  CELERY_WORKER_SHUTDOWN: (worker_name: string) =>
    `/celery/workers/${encodeURIComponent(worker_name)}/shutdown`,
  CELERY_TASK_REVOKE: (task_id: string) => `/celery/tasks/${task_id}/revoke`,
} as const;

// Common Constants
export const DEFAULT_PAGE_SIZE = 10;

// Activity Action Types
export const ACTIVITY_ACTIONS = {
  LOGIN: "login",
  LOGOUT: "logout",
  CREATE_ENTITY: "create_entity",
  UPDATE_ENTITY: "update_entity",
  DELETE_ENTITY: "delete_entity",
  CREATE_RELATIONSHIP: "create_relationship",
  UPDATE_RELATIONSHIP: "update_relationship",
  DELETE_RELATIONSHIP: "delete_relationship",
  RUN_PIPELINE: "run_pipeline",
  RESOLVE_CONFLICT: "resolve_conflict",
  CREATE_API_KEY: "create_api_key",
  REVOKE_API_KEY: "revoke_api_key",
  ASSIGN_ROLE: "assign_role",
  REMOVE_ROLE: "remove_role",
  UPDATE_PROFILE: "update_profile",
} as const;

export const SORT_DIRECTIONS = {
  ASC: "asc",
  DESC: "desc",
} as const;

// User Role Constants
export const USER_ROLES = {
  ADMIN: "admin",
  EXPERT: "expert",
  USER: "user",
} as const;

// Permission Constants
export const PERMISSIONS = {
  // Data source permissions
  DATASOURCE_READ: "datasource:read",
  DATASOURCE_WRITE: "datasource:write",
  DATASOURCE_DELETE: "datasource:delete",

  // Pipeline permissions
  PIPELINE_READ: "pipeline:read",
  PIPELINE_WRITE: "pipeline:write",
  PIPELINE_EXECUTE: "pipeline:execute",
  PIPELINE_DELETE: "pipeline:delete",

  // Knowledge graph permissions
  KG_READ: "kg:read",
  KG_SEARCH: "kg:search",
  KG_EDIT: "kg:edit",
  KG_DELETE: "kg:delete",

  // Quality & conflict permissions
  QUALITY_READ: "quality:read",
  QUALITY_EXPERT: "quality:expert",
  QUALITY_ADMIN: "quality:admin",

  // System administration
  USER_MANAGEMENT: "user:management",
  SYSTEM_CONFIG: "system:config",
  SYSTEM_MONITORING: "system:monitoring",

  // API access
  API_ACCESS: "api:access",
  API_UNLIMITED: "api:unlimited",
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: "Network error occurred. Please check your connection.",
  UNAUTHORIZED: "Unauthorized access. Please login again.",
  FORBIDDEN: "You do not have permission to perform this action.",
  NOT_FOUND: "The requested resource was not found.",
  VALIDATION_ERROR: "Please check your input and try again.",
  SERVER_ERROR: "An unexpected error occurred. Please try again later.",
  CONFLICT_ERROR: "A conflict occurred with the existing data.",
} as const;

// Validation Constants
export const VALIDATION = {
  PASSWORD_MIN_LENGTH: 8,
  USERNAME_MIN_LENGTH: 3,
  USERNAME_MAX_LENGTH: 50,
  EMAIL_MAX_LENGTH: 255,
  BIO_MAX_LENGTH: 500,
  API_KEY_LENGTH: 32,
} as const;

// Graph Constants
export const GRAPH_CONFIG = {
  DEFAULT_NODE_SIZE: 30,
  DEFAULT_EDGE_WIDTH: 2,
  DEFAULT_FONT_SIZE: 12,
  LAYOUTS: {
    FORCE: "force",
    HIERARCHICAL: "hierarchical",
    CIRCULAR: "circular",
  },
  THEMES: {
    LIGHT: {
      background: "#ffffff",
      node: "#1a73e8",
      edge: "#90a4ae",
      text: "#263238",
    },
    DARK: {
      background: "#1a1a1a",
      node: "#4dabf7",
      edge: "#546e7a",
      text: "#eceff1",
    },
  },
} as const;

// Date Formats
export const DATE_FORMATS = {
  DISPLAY: "PPpp", // e.g., "Apr 13, 2024, 12:00 PM"
  ISO: "yyyy-MM-dd'T'HH:mm:ss.SSSxxx",
  SHORT: "PP", // e.g., "Apr 13, 2024"
  TIME: "p", // e.g., "12:00 PM"
} as const;

export const SESSION_STORAGE_KEY = "vbkg_session";
