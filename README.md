# Knowledge Graph System for Banking Industry

<p align="center">
  <img src="docs/architecture/system_overview.png" alt="Knowledge Graph System Architecture" width="600"/>
</p>

## Introduction

Knowledge Graph System is a semi-automated platform for building and managing knowledge graphs specifically designed for the banking industry in Vietnam. The system combines natural language processing techniques, machine learning, and graph database technologies to create a comprehensive knowledge base from diverse data sources.

By leveraging AI-powered entity extraction and relationship analysis, the system enables financial institutions to organize and extract insights from complex banking data.

### Key Features

- **Automated Data Collection and Processing** from multiple formats (text, HTML, PDF, CSV, JSON)
- **Advanced Entity and Relationship Extraction** using OpenAI LLMs with Vietnamese language support
- **Vector Embeddings** for semantic search and entity resolution
- **Banking Domain Ontology Integration** for structured knowledge organization
- **Conflict Resolution System** with human oversight
- **Flexible API** for integration with external systems
- **Interactive Visualization Interface** for knowledge graph exploration
- **Comprehensive User Management and RBAC** for secure access control

## System Architecture

The system is organized into 5 main layers:

1. **Application Layer**: User interfaces and external integrations
2. **API Layer**: RESTful API for client applications
3. **Business Logic Layer**: User, knowledge, data source, and pipeline management
4. **Data Processing Layer**: Extraction, transformation, and enrichment
5. **Data Storage Layer**: Neo4j, PostgreSQL, and AWS S3

## Technology Stack

### Backend
- **FastAPI**: High-performance web framework
- **OpenAI API**: For entity extraction, relation extraction, and embeddings
- **Celery**: Distributed task queue for background processing

### Frontend
- **React**: Single-page application framework
- **TailwindCSS**: Utility-first CSS framework

### Databases
- **Neo4j**: Graph database for storing and querying the knowledge graph
- **PostgreSQL/Supabase**: Relational database for user management and metadata
- **AWS S3**: Object storage for source documents

### Infrastructure
- **Docker/Docker Compose**: Container orchestration
- **GitHub Actions**: Continuous Integration/Continuous Deployment

## Installation

### Requirements
- Docker and Docker Compose
- Python 3.9+
- Node.js 14+
- OpenAI API key

### Using Docker

```bash
# Clone repository
git clone https://github.com/yourusername/knowledge-graph-system.git
cd knowledge-graph-system

# Create environment file from template
cp .env.example .env
# Edit .env file with your configuration including OpenAI API key

# Start with Docker Compose
docker-compose up -d
