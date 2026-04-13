# Accounting AI MCP

> Small business accounting tools - invoicing, VAT, P&L, expense categorization, bank reconciliation

Built by **MEOK AI Labs** | [meok.ai](https://meok.ai)

## Features

| Tool | Description |
|------|-------------|
| `generate_invoice` | See tool docstring for details |
| `categorize_expenses` | See tool docstring for details |
| `calculate_vat` | See tool docstring for details |
| `profit_and_loss` | See tool docstring for details |
| `bank_reconciliation` | See tool docstring for details |

## Installation

```bash
pip install mcp
```

## Usage

### As an MCP Server

```bash
python server.py
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "accounting-ai-mcp": {
      "command": "python",
      "args": ["/path/to/accounting-ai-mcp/server.py"]
    }
  }
}
```

## Rate Limits

Free tier includes **30-50 calls per tool per day**. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with FastMCP by MEOK AI Labs
