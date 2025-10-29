# Intaste — Intelligent Assistive Search Technology

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

> **An open platform for intelligent, assistive, and human-centered search**

**Intaste** is an open-source AI-assisted search platform that combines enterprise-grade search with intelligent assistance. It uses search results as transparent evidence and provides concise, cited answers with LLM-powered understanding—keeping users in control while delivering actionable insights.

## Why Intaste?

- **🤖 AI-Powered Intelligence**: Natural language query understanding, relevance evaluation, and evidence-based answer composition with automatic citation
- **🏢 Enterprise Search Foundation**: Built on [Fess](https://fess.codelibs.org/), a battle-tested enterprise search platform with powerful crawling and indexing capabilities
- **🔒 Privacy-First**: Uses local LLM (Ollama) by default—no external API calls, no data leakage, full control over your search data
- **🌐 Open Source**: Apache 2.0 licensed with active community development and transparent architecture
- **⚡ Real-Time Streaming**: Server-Sent Events (SSE) for instant answer updates and responsive user experience
- **🌍 Multilingual**: Supports English, Japanese, Chinese (Simplified/Traditional), German, Spanish, and French

## System Requirements

- **Docker**: 24+ with Docker Compose v2+
- **Memory**: 6-8GB RAM recommended (includes OpenSearch, Fess, and Ollama)
- **CPU**: x86_64 (arm64 supported, depending on model compatibility)
- **GPU**: NVIDIA GPU recommended for faster responses (CPU-only mode available but slower)

> **Note**: Intaste uses Ollama with the `gpt-oss` model by default. GPU acceleration significantly improves response times, but the system works on CPU-only machines with increased latency.

## Quick Start (5 Minutes)

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/codelibs/intaste.git
cd intaste

# Setup environment variables
cp .env.example .env
sed -i.bak \
  -e "s/INTASTE_API_TOKEN=.*/INTASTE_API_TOKEN=$(openssl rand -hex 24)/" \
  -e "s/INTASTE_UID=.*/INTASTE_UID=$(id -u)/" \
  -e "s/INTASTE_GID=.*/INTASTE_GID=$(id -g)/" \
  .env

# Initialize data directories (Linux only, requires sudo)
sudo mkdir -p data/{opensearch,dictionary,ollama}
sudo chown -R $(id -u):$(id -g) data/
# Note: macOS/Windows users can skip this step
```

### 2. Start Services

```bash
# Start all services
docker compose up -d --build

# Pull LLM model (first time only)
docker compose exec ollama ollama pull gpt-oss

# Check health
curl -sS http://localhost:8000/api/v1/health && echo " - API OK"
curl -sS http://localhost:3000 > /dev/null && echo "UI OK"
```

> **First Startup**: OpenSearch and Fess initialization may take 3-5 minutes. Wait until health checks return successfully.

### 3. Access Intaste

Open your browser and navigate to:

```
http://localhost:3000
```

## Your First Search

Before you can search with Intaste, you need to configure Fess to crawl and index content.

### 1. Access Fess Admin Panel

Navigate to Fess:

```
http://localhost:8080/admin
```

**Default credentials**: `admin` / `admin`

### 2. Create a Crawler Configuration

1. Go to **Crawler > Web Crawler**
2. Click **Create New**
3. Configure the crawler:
   - **Name**: Give your crawler a descriptive name (e.g., "Company Documentation")
   - **URLs**: Enter the website URL you want to crawl (e.g., `https://example.com/docs/`)
   - **Max Access Count**: Set crawl depth limit (e.g., `1000`)
   - **Depth**: Set how many levels deep to crawl (e.g., `3`)
4. Click **Create**

### 3. Start Crawling

1. Go to **System > Scheduler**
2. Find the **Default Crawler** job
3. Click **Start Now**
4. Monitor crawl progress in **System > Crawling Info**

> **Tip**: Start with a small website (10-100 pages) for testing. Large crawls can take hours.

### 4. Perform Your First Search

1. Open Intaste at `http://localhost:3000`
2. Enter a natural language question related to your crawled content (e.g., "What are the system requirements?")
3. Wait for the AI-powered answer with citations like `[1][2]`
4. Click citation numbers to view source evidence in the sidebar
5. Try suggested follow-up questions to explore further

> **Note**: If no results appear, ensure crawling has completed and indexed documents are visible in Fess search (`http://localhost:8080/search`).

## Using Intaste

### Search Interface

- **Query Input**: Enter natural language questions or keywords
- **Answer Display**: View AI-generated answers with citation markers (`[1]`, `[2]`, etc.)
- **Evidence Panel**: Right sidebar shows source documents with relevance scores
- **Follow-ups**: Suggested questions appear below the answer for conversational exploration

### Language Selection

Intaste automatically responds in your selected language. Use the language selector in the top-right corner to switch between:

- English (en)
- Japanese (ja)
- Chinese Simplified (zh-CN)
- Chinese Traditional (zh-TW)
- German (de)
- Spanish (es)
- French (fr)

### Understanding Citations

Citations link answers to source evidence:

- `[1][2]`: Answer is supported by documents 1 and 2
- Click numbers to view source snippets in the sidebar
- Click **"Open in Fess"** to view the full original document

## Configuration

### Essential Environment Variables

Edit `.env` to customize Intaste:

| Variable | Default | Description |
|---|---|---|
| `INTASTE_API_TOKEN` | *(required)* | Authentication token for UI↔API communication |
| `INTASTE_DEFAULT_MODEL` | `gpt-oss` | Default Ollama model for LLM operations |
| `INTASTE_UID` / `INTASTE_GID` | `1000` | Docker user/group IDs for file permissions |
| `REQ_TIMEOUT_MS` | `180000` | Total request timeout (3 minutes) |

> **Security**: Always set `INTASTE_API_TOKEN` to a secure random value. Use `openssl rand -hex 24` to generate one.

### GPU Support

If you have an NVIDIA GPU:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Start services with GPU support:
   ```bash
   docker compose -f compose.yaml -f compose.gpu.yaml up -d
   ```
3. Verify GPU detection:
   ```bash
   docker compose exec ollama nvidia-smi
   ```

## Troubleshooting

| Issue | Solution |
|---|---|
| **Permission denied on `data/` directory** | Run: `sudo chown -R $(id -u):$(id -g) data/` |
| **UI shows "Connection failed"** | Check API health: `docker compose logs intaste-api` |
| **Search returns no results** | Verify Fess crawling completed: visit `http://localhost:8080/admin` |
| **LLM timeouts or 503 errors** | Ensure `ollama pull gpt-oss` completed. Check: `docker compose logs ollama` |
| **Slow responses on CPU** | This is expected without GPU. Consider using a lighter model or adding GPU support |
| **OpenSearch fails to start** | Increase Docker memory limit to 8GB or more in Docker Desktop settings |

## Next Steps

### For Developers

See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Development environment setup with hot reload
- Architecture overview and coding standards
- Testing guide and CI/CD workflows
- Contributing guidelines and PR process

### Full Documentation

- [TESTING.md](TESTING.md) - Comprehensive testing guide

## Community

- **Issues**: [GitHub Issues](https://github.com/codelibs/intaste/issues) for bugs and feature requests
- **Contributions**: We welcome contributions! See [DEVELOPMENT.md](DEVELOPMENT.md) to get started

## License

```
Apache License 2.0
Copyright (c) 2025 CodeLibs Project
```

See [LICENSE](LICENSE) for full details.

