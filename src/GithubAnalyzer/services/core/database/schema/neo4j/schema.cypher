// Node constraints
CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repository) REQUIRE r.url IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE (f.path, f.repository_id) IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Namespace) REQUIRE (n.name, n.file_id) IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (t:Type) REQUIRE (t.name, t.namespace_id) IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (f:Function) REQUIRE (f.name, f.namespace_id, f.type_id) IS UNIQUE;

// Node property existence constraints
CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repository) REQUIRE r.name IS NOT NULL;
CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.path IS NOT NULL;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Namespace) REQUIRE n.name IS NOT NULL;
CREATE CONSTRAINT IF NOT EXISTS FOR (t:Type) REQUIRE t.name IS NOT NULL;
CREATE CONSTRAINT IF NOT EXISTS FOR (f:Function) REQUIRE f.name IS NOT NULL;

// Node indexes
CREATE INDEX IF NOT EXISTS FOR (r:Repository) ON (r.name);
CREATE INDEX IF NOT EXISTS FOR (f:File) ON (f.path);
CREATE INDEX IF NOT EXISTS FOR (n:Namespace) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (t:Type) ON (t.name);
CREATE INDEX IF NOT EXISTS FOR (f:Function) ON (f.name);
CREATE INDEX IF NOT EXISTS FOR (p:Parameter) ON (p.name);
CREATE INDEX IF NOT EXISTS FOR (i:Import) ON (i.source_path);

// Indexes for relationship properties
CREATE INDEX IF NOT EXISTS FOR ()-[r:CALLS]-() ON (r.line_number);
CREATE INDEX IF NOT EXISTS FOR ()-[r:USES_TYPE]-() ON (r.usage_type);

// Full-text indexes for documentation search
CREATE FULLTEXT INDEX type_doc IF NOT EXISTS FOR (t:Type) ON EACH [t.documentation];
CREATE FULLTEXT INDEX function_doc IF NOT EXISTS FOR (f:Function) ON EACH [f.documentation];
CREATE FULLTEXT INDEX field_doc IF NOT EXISTS FOR (f:Field) ON EACH [f.documentation]; 