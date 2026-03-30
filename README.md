# NIST MCP Server

A professional Model Context Protocol (MCP) server providing comprehensive access to NIST cybersecurity frameworks and controls. Enables AI assistants and applications to query, analyze, and manage NIST security controls through a standardized, secure interface.

## 🚀 Quick Start

Get started with NIST's complete control catalog in minutes:

```bash
# Clone the repository
git clone https://github.com/skyionblue/nist-mcp-server.git
cd nist-mcp-server

# Install dependencies and download NIST data
./scripts/install.sh

# Run the server
uv run python -m nist_mcp.server
```

That's it! Your MCP server is now running with access to 1,196+ NIST security controls.

## 🔧 What You Can Do

### Core Control Operations
- **Browse all NIST SP 800-53 controls** (1,196 total: base controls + enhancements)
- **Get detailed control information** with implementation guidance
- **Search by keywords, families, or baseline levels**
- **Map controls to Cybersecurity Framework subcategories**

### Enterprise Compliance Support
- **CMMC 2.0 assessments** across all 5 maturity levels
- **FedRAMP readiness** for Low/Moderate/High impact systems
- **SP 800-171 CUI baseline** for protecting sensitive information
- **NIST Cybersecurity Framework** alignment and mapping

### Advanced Analysis
- **Gap analysis** against baseline requirements
- **Coverage assessments** across control families
- **Compliance mapping** to other frameworks (SOC2, ISO27001)
- **Risk evaluation** of control implementations

## 📖 Installation & Setup

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

### One-Command Setup (Recommended)

```bash
git clone https://github.com/your-username/nist-mcp-server.git
cd nist-mcp-server
./scripts/install.sh
uv run python -m nist_mcp.server
```

**That's it!** Your NIST MCP server is now running with 1,196+ controls.

### Manual Setup with uv (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/nist-mcp-server.git
cd nist-mcp-server

# 2. Install dependencies
uv sync

# 3. Download NIST data
uv run python scripts/download_nist_data.py

# 4. Start server
uv run python -m nist_mcp.server
```

### Manual Setup with pip

```bash
# 1. Clone the repository
git clone https://github.com/your-username/nist-mcp-server.git
cd nist-mcp-server

# 2. Install package in editable mode
pip install -e ".[dev]"

# 3. Download NIST data
python scripts/download_nist_data.py

# 4. Start server
python -m nist_mcp.server
```

## 🔌 Claude Code Integration

To use this MCP server with [Claude Code](https://claude.ai/code), follow these steps after completing the installation above.

### Option 1: CLI Command (Recommended)

From the project directory, run:

```bash
claude mcp add --transport stdio --scope user nist-mcp -- uv run python -m nist_mcp.server
```

- Use `--scope user` to make the server available across all your projects
- Use `--scope project` to share the configuration with your team (saves to `.mcp.json`)

### Option 2: Manual Configuration

Add the following to your `~/.claude.json` file:

```json
{
  "mcpServers": {
    "nist-mcp": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "-m", "nist_mcp.server"],
      "cwd": "/path/to/nist-mcp-server",
      "env": {}
    }
  }
}
```

Replace `/path/to/nist-mcp-server` with the actual path to your cloned repository.

### Verify the Configuration

```bash
claude mcp list          # List all configured MCP servers
claude mcp get nist-mcp  # Check this server's configuration
```

Once configured, use the `/mcp` command within Claude Code to see connected servers and their available tools.

## 🛠️ Practical Examples

Here are real examples of how to use the NIST MCP tools:

### Basic Control Lookup

**"What does AC-1 say?"**
```json
// Call: get_control("AC-1")
{
  "id": "ac-1",
  "title": "Policy and Procedures",
  "class": "SP800-53",
  "family": "AC",
  "parts": [
    {
      "name": "statement",
      "prose": "The organization develops and maintains a comprehensive security policy..."
    }
  ],
  "links": [...]
}
```

**"Show me all Access Control family controls"**
```json
// Call: get_control_family("AC")
{
  "family": "AC",
  "name": "Access Control",
  "description": "The AC family contains controls...",
  "total_controls": 57,
  "base_controls": 25,
  "enhancements": 32,
  "controls": [...]
}
```

### Compliance Analysis

**"Do we meet Moderate baseline requirements?"**
```json
// Call: gap_analysis(implemented_controls=["AC-1", "AU-1"], target_baseline="moderate")
{
  "total_required": 177,
  "implemented_count": 2,
  "missing_count": 175,
  "compliance_percentage": 1.13,
  "critical_gaps": ["Risk Assessment", "Configuration Management"],
  "next_priorities": ["AC-2", "IA-2", "AU-2"]
}
```

**"What's our CMMC Level 2 readiness?"**
```json
// Call: cmmc_compliance_assessment(implemented_controls=["AC-1", "IA-2"], target_level=2)
{
  "current_level": 1,
  "target_level": 2,
  "achieved_domains": ["AC", "IA"],
  "missing_domains": ["CM", "CP", "IR"],
  "progress_percentage": 23.5,
  "next_steps": ["Implement CM-2", "Add CP-9 controls"]
}
```

### Risk Assessments

**"How risky is our current access control implementation?"**
```json
// Call: risk_assessment_helper(control_ids=["AC-1", "AC-2", "IA-3"])
{
  "overall_risk_score": 7.3,
  "critical_gaps": ["AC-6 (Least Privilege)", "AC-18 (Wireless Access)"],
  "recommendations": [
    "Implement multi-factor authentication (IA-3)",
    "Review access control policies (AC-1)",
    "Add session timeout controls"
  ]
}
```

### Enterprise Framework Alignment

**"Map our controls to NIST CSF functions"**
```json
// Call: get_control_mappings("AC-1")
{
  "control_id": "AC-1",
  "csf_mappings": ["PR.IP-1", "PR.IP-6"],
  "functions": ["Protect"],
  "categories": ["Identity Management"],
  "rationale": "Policy framework supports identity protection"
}
```

**"Prepare for FedRAMP Moderate authorization"**
```json
// Call: get_baseline_controls("moderate")
{
  "baseline": "Moderate",
  "total_controls": 177,
  "required_families": {
    "AC": 12, "AU": 9, "CA": 5,
    "CM": 10, "IA": 8, "IR": 6,
    "MP": 4, "PE": 8, "PS": 3,
    "RA": 5, "SC": 45, "SI": 16,
    "SA": 6, "AT": 1, "PL": 2
  },
  "implementation_timeline": "12-18 months"
}
```

## 📚 MCP Tool Reference

### Core Control Operations
- **`list_controls()`** - Browse all 1,196 NIST controls
- **`get_control("AC-1")`** - Get detailed control info with implementation guidance
- **`search_controls("access", "AC", 10)`** - Search controls by keyword within families
- **`get_control_family("AC")`** - Get complete access control family (57 total controls)

### Framework & Compliance
- **`get_baseline_controls("moderate")`** - NIST baselines for system categorization
- **`cmmc_compliance_assessment(current_controls, 3)`** - CMMC readiness assessment
- **`fedramp_readiness_assessment(controls, "saas")`** - FedRAMP cloud readiness
- **`get_sp800171_baseline()`** - CUI protection baseline (DOD contractors)

### Advanced Analysis
- **`gap_analysis(implemented, "high")`** - Identify missing controls against baselines
- **`analyze_control_coverage(["AC-1", "AU-1"])`** - Assess control family coverage
- **`compliance_mapping("ISO27001", controls)`** - Cross-framework mapping

### Cybersecurity Framework
- **`get_csf_framework()`** - Complete NIST CSF 2.0 with all functions
- **`search_csf_subcategories("multi-factor")`** - Find relevant CSF subcategories
- **`csf_to_controls_mapping("PR.AC-1")`** - Map CSF requirements to controls

## Project Structure

```
nist-mcp-server/
├── src/nist_mcp/           # Main package
│   ├── server.py           # MCP server implementation
│   ├── data/               # Data loading and caching
│   │   └── loader.py       # NIST data loader
│   ├── tools/              # MCP tools (future expansion)
│   └── utils/              # Utility functions
├── data/                   # NIST data sources
│   ├── nist-sources/       # Official NIST data
│   │   ├── sp800-53/       # SP 800-53 controls and baselines
│   │   ├── sp800-171/      # SP 800-171 CUI baseline profiles
│   │   ├── cmmc/           # CMMC framework and maturity levels
│   │   ├── fedramp/        # FedRAMP framework and impact levels
│   │   ├── csf/            # Cybersecurity Framework data
│   │   └── mappings/       # Control-to-CSF mappings
│   ├── oscal-schemas/      # OSCAL JSON schemas
│   └── examples/           # Example OSCAL documents
├── scripts/                # Utility scripts
│   └── download_nist_data.py # Data download script and framework creation
├── tools/                  # Additional control tools
│   └── control_tools.py    # Control management utilities
└── tests/                  # Test suite
```

## 📋 Important Notes

### Data Sources
Uses official public domain NIST data:
- **SP 800-53 Rev 5** (1,196 controls)
- **Cybersecurity Framework 2.0**
- **OSCAL schemas** for document validation

### Development & Testing
```bash
uv sync --dev                         # Install dev tools
uv run make test                      # Run full test suite
uv run make test-security             # Security testing only
uv run python -m nist_mcp.server      # Start server
```

### License
- **MIT License** (code)
- **Public Domain** (NIST data)
- **Apache 2.0** (OSCAL schemas)

### Support
- [Documentation](docs/README.md)
- [Create Issue](https://github.com/your-username/nist-mcp-server/issues)
- [Contributing Guide](CONTRIBUTING.md)
