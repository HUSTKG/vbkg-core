-- Clean up existing role-permission relationships first
TRUNCATE public.role_permissions CASCADE;

-- Clean up and reseed roles
DELETE FROM public.roles;
INSERT INTO public.roles (name, description) VALUES
    ('admin', 'Administrator with full system access');
-- Clean up and reseed permissions
DELETE FROM public.permissions;
INSERT INTO public.permissions (name, description) VALUES
    ('viewer', 'User with read-only access');

-- Seed default permissions
INSERT INTO public.permissions (name, description) VALUES
    ('manage_users', 'Can manage user accounts and roles'),
    ('manage_pipelines', 'Can create and manage data pipelines'),
    ('manage_ontology', 'Can modify ontology and mappings'),
    ('upload_data', 'Can upload new data sources'),
    ('run_queries', 'Can execute queries against the knowledge graph'),
    ('view_data', 'Can view knowledge graph data');

-- Associate permissions with roles
INSERT INTO public.role_permissions (role_id, permission_id) 
SELECT r.id, p.id 
FROM public.roles r, public.permissions p 
WHERE r.name = 'admin';  -- Admin gets all permissions

INSERT INTO public.role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM public.roles r, public.permissions p 
WHERE r.name = 'data_curator' 
AND p.name IN ('manage_ontology', 'upload_data', 'run_queries', 'view_data');

INSERT INTO public.role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM public.roles r, public.permissions p 
WHERE r.name = 'analyst' 
AND p.name IN ('run_queries', 'view_data');

INSERT INTO public.role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM public.roles r, public.permissions p 
WHERE r.name = 'viewer' 
AND p.name IN ('view_data');

-- Seed some initial FIBO classes
INSERT INTO public.fibo_classes (uri, label, description) VALUES
    ('fibo:FI/BusinessEntities/FinancialInstitutions/Bank', 'Bank', 'A financial institution that accepts deposits and channels those deposits into lending activities'),
    ('fibo:FI/FinancialInstruments/FinancialProduct', 'Financial Product', 'A product provided to consumers and businesses by financial institutions'),
    ('fibo:FI/BusinessEntities/Accounts/Account', 'Account', 'A formal banking, brokerage, or business relationship established to provide for regular services, dealings, and other financial transactions'),
    ('fibo:BE/LegalEntities/LegalPerson', 'Legal Person', 'Any human or non-human entity that is treated as a person for legal purposes');

-- Seed some initial FIBO properties
INSERT INTO public.fibo_properties (uri, label, description, property_type) VALUES
    ('fibo:hasAccount', 'has account', 'Relates a person or organization to their financial accounts', 'object'),
    ('fibo:provides', 'provides', 'Relates a financial institution to the products or services it offers', 'object'),
    ('fibo:accountHolder', 'account holder', 'The legal person who owns an account', 'object'),
    ('fibo:balance', 'balance', 'The current balance of an account', 'datatype'),
    ('fibo:accountNumber', 'account number', 'The unique identifier for an account', 'datatype');

-- Seed some initial data sources
INSERT INTO public.data_sources (name, description, source_type, connection_details, credentials, is_active, created_by) VALUES
    ('FIBO Core', 'Core FIBO ontology files', 'file', '{"format": "owl", "version": "latest"}', NULL, true, NULL),
    ('Banking Terms', 'Standard banking terminology and relationships', 'file', '{"delimiter": ",", "encoding": "utf-8"}', NULL, true, NULL);

-- Seed some example entity mappings
INSERT INTO public.entity_mappings (entity_type, fibo_class_id, confidence, created_by, is_verified) VALUES
    ('checking_account', (SELECT id FROM public.fibo_classes WHERE uri = 'fibo:FI/BusinessEntities/Accounts/Account'), 1.0, NULL, true),
    ('bank', (SELECT id FROM public.fibo_classes WHERE uri = 'fibo:FI/BusinessEntities/FinancialInstitutions/Bank'), 1.0, NULL, true);

-- Seed some example relationship mappings
INSERT INTO public.relationship_mappings (relationship_type, fibo_property_id, confidence, created_by, is_verified) VALUES
    ('has_account', (SELECT id FROM public.fibo_properties WHERE uri = 'fibo:hasAccount'), 1.0, NULL, true),
    ('account_owner', (SELECT id FROM public.fibo_properties WHERE uri = 'fibo:accountHolder'), 1.0, NULL, true);

-- Seed some example saved queries
INSERT INTO public.saved_queries (name, description, query_type, query_text, parameters, is_public, created_by) VALUES
    ('Find All Banks', 'Lists all banking institutions', 'cypher', 'MATCH (b:Bank) RETURN b', '{}', true, NULL),
    ('Account Holders', 'Shows all account holders and their accounts', 'cypher', 'MATCH (p:Person)-[r:hasAccount]->(a:Account) RETURN p, r, a', '{}', true, NULL);

COMMIT;

