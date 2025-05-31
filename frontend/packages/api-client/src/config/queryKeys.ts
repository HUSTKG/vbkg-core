import {
  IGlobalSearchRequest,
  IReadDomainsRequest,
  IReadEntityTypesRequest,
  IGetUsersRequest,
  IReadRelationshipTypesRequest,
  IGetCeleryWorkersRequest,
  IGetCeleryTasksRequest,
  ISearchRelationshipsRequest,
  IGetUserActivityRequest,
  ISearchKGEntitiesRequest,
} from "@vbkg/types";

export const QueryKeys = Object.freeze({
  datasources: {
    list: (filter?: any) => ["datasources", "list", filter],
    details: (id: string) => ["datasources", "details", id],
    create: () => ["datasources", "create"],
    update: (id: string) => ["datasources", "update", id],
    delete: (id: string) => ["datasources", "delete", id],
    pipeline_templates: (id: string) => ["pipeline_templates", id],
  },
  fileUploads: {
    list: (filter?: any) => ["fileUploads", "list", filter],
    details: (id: string) => ["fileUploads", "details", id],
    content: (id: string) => ["fileContent", id],
    publicUrl: (id: string) => ["filePublicUrl", id],
  },
  knowledgeGraph: {
    all: () => ["knowledge-graph"] as const,

    // Entities
    entities: () => [...QueryKeys.knowledgeGraph.all(), "entities"] as const,
    entity: (entityId: string, includeRelationships?: boolean) =>
      [
        ...QueryKeys.knowledgeGraph.entities(),
        entityId,
        { includeRelationships },
      ] as const,
    entitiesSearch: (params: ISearchKGEntitiesRequest) =>
      [...QueryKeys.knowledgeGraph.entities(), "search", params] as const,
    relationshipsSearch: (params: ISearchRelationshipsRequest) =>
      [...QueryKeys.knowledgeGraph.relationships(), "search", params] as const,
    entityTypes: () =>
      [...QueryKeys.knowledgeGraph.entities(), "types"] as const,
    entityNeighbors: (
      entityId: string,
      maxDepth?: number,
      relationshipTypes?: string[],
      limitPerLevel?: number,
    ) =>
      [
        ...QueryKeys.knowledgeGraph.entities(),
        entityId,
        "neighbors",
        { maxDepth, relationshipTypes, limitPerLevel },
      ] as const,

    // Relationships
    relationships: () =>
      [...QueryKeys.knowledgeGraph.all(), "relationships"] as const,
    relationship: (relationshipId: string) =>
      [...QueryKeys.knowledgeGraph.relationships(), relationshipId] as const,
    entityRelationships: (
      entityId: string,
      relationshipTypes?: string[],
      direction?: string,
      limit?: number,
      offset?: number,
    ) =>
      [
        ...QueryKeys.knowledgeGraph.entities(),
        entityId,
        "relationships",
        { relationshipTypes, direction, limit, offset },
      ] as const,

    // Graph traversal
    traversal: () => [...QueryKeys.knowledgeGraph.all(), "traversal"] as const,
    subgraph: (
      entityId: string,
      radius?: number,
      maxNodes?: number,
      relationshipTypes?: string[],
    ) =>
      [
        ...QueryKeys.knowledgeGraph.traversal(),
        "subgraph",
        entityId,
        { radius, maxNodes, relationshipTypes },
      ] as const,
    paths: (sourceId: string, targetId: string, params?: any) =>
      [
        ...QueryKeys.knowledgeGraph.traversal(),
        "paths",
        sourceId,
        targetId,
        params,
      ] as const,

    // Analytics
    analytics: () => [...QueryKeys.knowledgeGraph.all(), "analytics"] as const,
    stats: () => [...QueryKeys.knowledgeGraph.analytics(), "stats"] as const,
    investmentInsights: (entityType: string, limit?: number) =>
      [
        ...QueryKeys.knowledgeGraph.analytics(),
        "investment-insights",
        { entityType, limit },
      ] as const,

    // Search
    search: () => [...QueryKeys.knowledgeGraph.all(), "search"] as const,
    globalSearch: (params: IGlobalSearchRequest) =>
      [...QueryKeys.knowledgeGraph.search(), "global", params] as const,
  },
  quality: {
    all: () => ["quality"] as const,

    // Dashboard
    dashboard: () => [...QueryKeys.quality.all(), "dashboard"] as const,
    report: (daysBack?: number) =>
      [...QueryKeys.quality.all(), "report", { daysBack }] as const,

    // Conflicts
    conflicts: {
      all: () => [...QueryKeys.quality.all(), "conflicts"] as const,
      list: (params?: any) =>
        [...QueryKeys.quality.conflicts.all(), "list", params] as const,
    },
  },
  validationRules: {
    all: () => ["validation-rules"] as const,
    // Rules
    rules: () => [...QueryKeys.validationRules.all(), "rules"] as const,
    lists: () => [...QueryKeys.validationRules.rules(), "list"],
    list: (params?: any) =>
      [...QueryKeys.validationRules.lists(), params] as const,
    details: (ruleId: string) =>
      [...QueryKeys.validationRules.rules(), ruleId] as const,

    // Executions
    executions: {
      all: () => [...QueryKeys.validationRules.all(), "executions"] as const,
      lists: () => [...QueryKeys.validationRules.executions.all(), "list"],
      list: (params?: any) =>
        [...QueryKeys.validationRules.executions.lists(), params] as const,
      details: (executionId: string) =>
        [...QueryKeys.validationRules.executions.all(), executionId] as const,
    },

    // Violations
    violations: {
      all: () => [...QueryKeys.validationRules.all(), "violations"] as const,
      lists: () => [...QueryKeys.validationRules.violations.all(), "list"],
      list: (params?: any) =>
        [...QueryKeys.validationRules.violations.lists(), params] as const,
      details: (violationId: string) =>
        [...QueryKeys.validationRules.violations.all(), violationId] as const,
    },

    // Dashboard & Statistics
    dashboard: () => [...QueryKeys.validationRules.all(), "dashboard"] as const,
    summary: () => [...QueryKeys.validationRules.all(), "summary"] as const,
    performance: (ruleIds?: string[]) =>
      [...QueryKeys.validationRules.all(), "performance", { ruleIds }] as const,

    // Templates
    templates: () => [...QueryKeys.validationRules.all(), "templates"] as const,
    template: (templateId: string) =>
      [...QueryKeys.validationRules.templates(), templateId] as const,
  },
  // =============================================
  // DOMAIN QUERY KEYS - NEW SECTION
  // =============================================
  domains: {
    all: () => ["domains"] as const,

    // Domain queries
    list: (params?: IReadDomainsRequest) =>
      [...QueryKeys.domains.all(), "list", params] as const,
    details: (id: string, include_types?: boolean) =>
      [...QueryKeys.domains.all(), "details", id, { include_types }] as const,
    stats: (id: string) => [...QueryKeys.domains.all(), "stats", id] as const,

    // Entity Types
    entityTypes: {
      all: () => [...QueryKeys.domains.all(), "entity-types"] as const,
      list: (params?: IReadEntityTypesRequest) =>
        [...QueryKeys.domains.entityTypes.all(), "list", params] as const,
      details: (
        id: string,
        include_domains?: boolean,
        include_usage?: boolean,
      ) =>
        [
          ...QueryKeys.domains.entityTypes.all(),
          "details",
          id,
          { include_domains, include_usage },
        ] as const,
      byDomain: (domain_name: string, primary_only?: boolean) =>
        [
          ...QueryKeys.domains.entityTypes.all(),
          "by-domain",
          domain_name,
          { primary_only },
        ] as const,
    },

    // Relationship Types
    relationshipTypes: {
      all: () => [...QueryKeys.domains.all(), "relationship-types"] as const,
      list: (params?: IReadRelationshipTypesRequest) =>
        [...QueryKeys.domains.relationshipTypes.all(), "list", params] as const,
      details: (
        id: string,
        include_domains?: boolean,
        include_usage?: boolean,
      ) =>
        [
          ...QueryKeys.domains.relationshipTypes.all(),
          "details",
          id,
          { include_domains, include_usage },
        ] as const,
      byDomain: (domain_name: string, primary_only?: boolean) =>
        [
          ...QueryKeys.domains.relationshipTypes.all(),
          "by-domain",
          domain_name,
          { primary_only },
        ] as const,
      compatible: (params: {
        source_entity_type_id: number;
        target_entity_type_id?: number;
        domain_ids?: number[];
      }) =>
        [
          ...QueryKeys.domains.relationshipTypes.all(),
          "compatible",
          params,
        ] as const,
    },

    // Analytics
    analytics: {
      all: () => [...QueryKeys.domains.all(), "analytics"] as const,
      overview: () =>
        [...QueryKeys.domains.analytics.all(), "overview"] as const,
    },

    // Validation
    validation: {
      all: () => [...QueryKeys.domains.all(), "validation"] as const,
      typeConstraints: (params: {
        entity_type_id?: number;
        relationship_type_id?: number;
        source_entity_type_id?: number;
        target_entity_type_id?: number;
      }) =>
        [
          ...QueryKeys.domains.validation.all(),
          "type-constraints",
          params,
        ] as const,
    },
  },
  // =============================================
  // END DOMAIN QUERY KEYS
  // =============================================
  celery: {
    all: () => ["celery"] as const,
    dashboard: () => [...QueryKeys.celery.all(), "dashboard"] as const,
    workers: {
      all: () => [...QueryKeys.celery.all(), "workers"] as const,
      list: (params?: IGetCeleryWorkersRequest) =>
        [...QueryKeys.celery.workers.all(), "list", params] as const,
      detail: (worker_name: string) =>
        [...QueryKeys.celery.workers.all(), "detail", worker_name] as const,
      stats: () => [...QueryKeys.celery.workers.all(), "stats"] as const,
    },
    tasks: {
      all: () => [...QueryKeys.celery.all(), "tasks"] as const,
      list: (params?: IGetCeleryTasksRequest) =>
        [...QueryKeys.celery.tasks.all(), "list", params] as const,
      detail: (task_id: string) =>
        [...QueryKeys.celery.tasks.all(), "detail", task_id] as const,
    },
    stats: () => [...QueryKeys.celery.all(), "stats"] as const,
    health: () => [...QueryKeys.celery.all(), "health"] as const,
  },
  users: {
    all: () => ["users"] as const,
    lists: () => [...QueryKeys.users.all(), "list"] as const,
    list: (params?: IGetUsersRequest) =>
      [...QueryKeys.users.lists(), params] as const,
    details: () => [...QueryKeys.users.all(), "detail"] as const,
    detail: (user_id: string) =>
      [...QueryKeys.users.details(), user_id] as const,
    me: () => [...QueryKeys.users.all(), "me"] as const,
    roles: () => [...QueryKeys.users.all(), "roles"] as const,
    permissions: () => [...QueryKeys.users.all(), "permissions"] as const,
    apiKeys: () => [...QueryKeys.users.all(), "api-keys"] as const,
    activity: {
      all: () => [...QueryKeys.users.all(), "activity"] as const,
      my: (params?: IGetUserActivityRequest) =>
        [...QueryKeys.users.activity.all(), "my", params] as const,
      user: (user_id: string, params?: IGetUserActivityRequest) =>
        [...QueryKeys.users.activity.all(), "user", user_id, params] as const,
    },
    stats: () => [...QueryKeys.users.all(), "stats"] as const,
  },
});
