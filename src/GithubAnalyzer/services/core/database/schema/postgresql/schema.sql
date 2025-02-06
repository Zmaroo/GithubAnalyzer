-- Core tables for code entities
CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(512) NOT NULL,
    resource_type VARCHAR(50) NOT NULL DEFAULT 'codebase',
    description TEXT,
    default_branch VARCHAR(255) NOT NULL DEFAULT 'main',
    last_analyzed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    path VARCHAR(1024) NOT NULL,
    language VARCHAR(50),
    last_modified TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, path)
);

CREATE TABLE IF NOT EXISTS namespaces (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES namespaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'package', 'module', 'namespace'
    documentation TEXT,
    start_line INTEGER,
    end_line INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS types (
    id SERIAL PRIMARY KEY,
    namespace_id INTEGER REFERENCES namespaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    kind VARCHAR(50) NOT NULL, -- 'class', 'interface', 'trait', 'enum', 'type_alias'
    documentation TEXT,
    modifiers TEXT[], -- ['public', 'abstract', etc.]
    start_line INTEGER,
    end_line INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS type_relationships (
    id SERIAL PRIMARY KEY,
    source_type_id INTEGER REFERENCES types(id) ON DELETE CASCADE,
    target_type_id INTEGER REFERENCES types(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- 'extends', 'implements', 'uses'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS type_parameters (
    id SERIAL PRIMARY KEY,
    type_id INTEGER REFERENCES types(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    constraints TEXT[], -- Type constraints/bounds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS functions (
    id SERIAL PRIMARY KEY,
    namespace_id INTEGER REFERENCES namespaces(id) ON DELETE CASCADE,
    type_id INTEGER REFERENCES types(id) ON DELETE CASCADE, -- For methods
    name VARCHAR(255) NOT NULL,
    kind VARCHAR(50) NOT NULL, -- 'function', 'method', 'constructor', 'lambda'
    documentation TEXT,
    modifiers TEXT[], -- ['public', 'static', etc.]
    return_type TEXT,
    is_async BOOLEAN DEFAULT FALSE,
    is_generator BOOLEAN DEFAULT FALSE,
    start_line INTEGER,
    end_line INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parameters (
    id SERIAL PRIMARY KEY,
    function_id INTEGER REFERENCES functions(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type TEXT,
    default_value TEXT,
    is_variadic BOOLEAN DEFAULT FALSE,
    is_optional BOOLEAN DEFAULT FALSE,
    position INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fields (
    id SERIAL PRIMARY KEY,
    type_id INTEGER REFERENCES types(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    field_type TEXT,
    documentation TEXT,
    modifiers TEXT[], -- ['private', 'static', etc.]
    default_value TEXT,
    start_line INTEGER,
    end_line INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS imports (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    source_path TEXT NOT NULL,
    alias TEXT,
    is_type_only BOOLEAN DEFAULT FALSE,
    start_line INTEGER,
    end_line INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dependencies (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(255),
    type VARCHAR(50) NOT NULL, -- 'runtime', 'dev', 'peer', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS code_snippets (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    file_path VARCHAR(1024) NOT NULL,
    code_text TEXT NOT NULL,
    language VARCHAR(50),
    embedding vector(768),
    metadata JSONB,
    is_supported BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_files_repo_id ON files(repository_id);
CREATE INDEX IF NOT EXISTS idx_namespaces_file_id ON namespaces(file_id);
CREATE INDEX IF NOT EXISTS idx_types_namespace_id ON types(namespace_id);
CREATE INDEX IF NOT EXISTS idx_functions_namespace_id ON functions(namespace_id);
CREATE INDEX IF NOT EXISTS idx_functions_type_id ON functions(type_id);
CREATE INDEX IF NOT EXISTS idx_parameters_function_id ON parameters(function_id);
CREATE INDEX IF NOT EXISTS idx_fields_type_id ON fields(type_id);
CREATE INDEX IF NOT EXISTS idx_imports_file_id ON imports(file_id);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_types_documentation_fts ON types USING GIN (to_tsvector('english', documentation));
CREATE INDEX IF NOT EXISTS idx_functions_documentation_fts ON functions USING GIN (to_tsvector('english', documentation));
CREATE INDEX IF NOT EXISTS idx_fields_documentation_fts ON fields USING GIN (to_tsvector('english', documentation));

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_functions_composite ON functions(namespace_id, type_id, name);
CREATE INDEX IF NOT EXISTS idx_types_composite ON types(namespace_id, name, kind); 