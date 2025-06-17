import { EntityType, RelationshipType } from "../domain";

export type FIBOClassBase = {
	uri: string;
	label?: string;
	description?: string;
	domain?: string;
	properties?: Record<string, any>;
};

export type FIBOClassCreate = FIBOClassBase & {
	parent_class_uri?: string;
	is_custom: boolean;
};

export type FIBOClassUpdate = Partial<FIBOClassBase> & {
	parent_class_uri?: string;
};

export type FIBOClass = FIBOClassBase & {
	id: number;
	parent_class_id?: number;
	is_custom: boolean;
	created_at: string;
	updated_at: string;
};

export type FIBOPropertyBase = {
	uri: string;
	label?: string;
	description?: string;
	domain?: string;
	property_type: "object" | "datatype";
};

export type FIBOPropertyCreate = FIBOPropertyBase & {
	domain_class_uri?: string;
	range_class_uri?: string;
	is_custom: boolean;
};

export type FIBOPropertyUpdate = Partial<FIBOPropertyBase> & {
	domain_class_uri?: string;
	range_class_uri?: string;
	property_type?: "object" | "datatype";
};

export type FIBOProperty = FIBOPropertyBase & {
	id: number;
	domain_class_id?: number;
	range_class_id?: number;
	is_custom: boolean;
	created_at: string;
	updated_at: string;
};

// Updated Mapping Types
export type MappingStatus = "pending" | "mapped" | "rejected" | "needs_review";

export type EntityMappingBase = {
	entity_type?: string; // Legacy field
	entity_type_id?: number;
	ontology_class_uri: string;
	confidence?: number;
	is_verified: boolean;
	mapping_status: MappingStatus;
	mapping_notes?: string;
	suggestions: Array<{
		reasoning: string;
		confidence: number;
		is_new_class: boolean;
		suggested_class: string;
	}>;
	auto_mapped: boolean;
};

export type EntityMappingCreate = EntityMappingBase;

export type EntityMappingUpdate = Partial<EntityMappingBase>;

export type EntityMapping = EntityMappingBase & {
	id: number;
	created_by?: string;
	created_at: string;
	updated_at: string;
	reviewed_by?: string;
	reviewed_at?: string;
	entity_type_info?: EntityType;
};

export type RelationshipMappingBase = {
	relationship_type?: string; // Legacy field
	relationship_type_id?: number;
	ontology_property_uri: string;
	confidence?: number;
	is_verified: boolean;
	mapping_status: MappingStatus;
	mapping_notes?: string;
	suggestions: Array<{
		reasoning: string;
		confidence: number;
		is_new_property: boolean;
		suggested_property: string;
	}>;
	auto_mapped: boolean;
};

export type RelationshipMappingCreate = RelationshipMappingBase;

export type RelationshipMappingUpdate = Partial<RelationshipMappingBase>;

export type RelationshipMapping = RelationshipMappingBase & {
	id: number;
	created_by?: string;
	created_at: string;
	updated_at: string;
	reviewed_by?: string;
	reviewed_at?: string;
	relationship_type_info?: RelationshipType;
	ontology_property?: FIBOProperty;
};

// Request/Response Types
export type OntologyImportRequest = {
	file_id?: string;
	url?: string;
	format: "rdf" | "owl" | "ttl";
};

export type OntologyImportResponse = {
	success: boolean;
	message: string;
	classes_imported?: number;
	properties_imported?: number;
	errors?: string[];
};

// Suggestion Types
export type EntityTypeSuggestion = {
	entity_type: EntityType;
	confidence: number;
	reason: string;
};

export type RelationshipTypeSuggestion = {
	relationship_type: RelationshipType;
	confidence: number;
	reason: string;
};

export type FIBOClassSuggestion = {
	ontology_class: FIBOClass;
	confidence: number;
	reason: string;
};

export type FIBOPropertySuggestion = {
	ontology_property: FIBOProperty;
	confidence: number;
	reason: string;
};

// Bulk Operations
export type BulkEntityMappingCreate = {
	mappings: EntityMappingCreate[];
};

export type BulkRelationshipMappingCreate = {
	mappings: RelationshipMappingCreate[];
};

export type BulkMappingResponse = {
	success: number;
	failed: number;
	errors?: string[];
};

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
