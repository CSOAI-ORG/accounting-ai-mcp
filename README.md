<div align="center">

# Accounting Ai MCP

**Accounting AI MCP Server**

[![PyPI](https://img.shields.io/pypi/v/meok-accounting-ai-mcp)](https://pypi.org/project/meok-accounting-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Accounting AI MCP Server
Small business accounting tools powered by MEOK AI Labs.

## Tools

| Tool | Description |
|------|-------------|
| `generate_invoice` | Generate a professional invoice with line items, VAT, and totals. |
| `categorize_expenses` | Automatically categorize business expenses by type. |
| `calculate_vat` | Calculate VAT/tax for any country with support for inclusive/exclusive amounts. |
| `profit_and_loss` | Generate a profit and loss statement from income and expense records. |
| `bank_reconciliation` | Reconcile bank statement transactions against book records. |

## Installation

```bash
pip install meok-accounting-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "accounting-ai": {
      "command": "python",
      "args": ["-m", "meok_accounting_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 5 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
