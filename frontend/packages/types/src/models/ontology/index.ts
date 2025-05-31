export interface OntologyClass {
  id: string;
  name: string;
  description?: string;
  properties: OntologyProperty[];
  relations: OntologyRelation[];
  metadata: {
    createdAt: Date;
    updatedAt: Date;
    createdBy: string;
    updatedBy: string;
    version: string;
  };
}

export interface OntologyProperty {
  name: string;
  type: "string" | "number" | "boolean" | "date" | "enum" | "object" | "array";
  required: boolean;
  defaultValue?: unknown;
  constraints?: PropertyConstraints;
  description?: string;
}

export interface OntologyRelation {
  name: string;
  targetClass: string;
  cardinality: "one-to-one" | "one-to-many" | "many-to-many";
  inverse?: string;
  required: boolean;
  description?: string;
}

export interface PropertyConstraints {
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  minimum?: number;
  maximum?: number;
  enum?: string[];
  items?: OntologyProperty; // For array types
  properties?: Record<string, OntologyProperty>; // For object types
}
