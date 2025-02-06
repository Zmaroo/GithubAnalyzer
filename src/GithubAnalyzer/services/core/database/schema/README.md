# Database Schemas

This directory contains the database schemas for the GithubAnalyzer project.

## Structure

- `postgresql/`: PostgreSQL schema files
  - `schema.sql`: Main schema file containing table definitions, indexes, and constraints
  
- `neo4j/`: Neo4j schema files
  - `schema.cypher`: Main schema file containing node definitions, relationships, and indexes

## Schema Overview

### PostgreSQL Schema

The PostgreSQL schema defines the relational structure for:

- Repositories and files
- Code elements (functions, classes, etc.)
- Type system and relationships
- Documentation and metadata
- Search indexes

### Neo4j Schema

The Neo4j schema defines the graph structure for:

- Code relationships and dependencies
- Call hierarchies
- Type hierarchies
- Import/export relationships
- Search indexes

## Usage

These schema files are automatically loaded by their respective database services:

- `PostgresService.create_tables()` loads `postgresql/schema.sql`
- `Neo4jService.setup_constraints()` loads `neo4j/schema.cypher`

## Maintenance

When updating schemas:

1. Always maintain backward compatibility or provide migration scripts
2. Keep both PostgreSQL and Neo4j schemas in sync for overlapping concepts
3. Update indexes based on query patterns and performance needs
4. Document any schema changes in the service's changelog
