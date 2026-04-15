# Accounting AI MCP Server

> By [MEOK AI Labs](https://meok.ai) — Small business accounting tools with invoicing, VAT, and reconciliation

## Installation

```bash
pip install accounting-ai-mcp
```

## Usage

```bash
# Run standalone
python server.py

# Or via MCP
mcp install accounting-ai-mcp
```

## Tools

### `generate_invoice`
Generate a professional invoice with line items, VAT, and totals. Supports 20+ country VAT rates.

**Parameters:**
- `business_name` (str): Your business/company name
- `client_name` (str): Client or customer name
- `items` (list[dict]): List of dicts with keys: description, quantity, unit_price
- `currency` (str): Currency code (GBP, USD, EUR, etc.)
- `country_code` (str): ISO country code for VAT rate
- `invoice_number` (str): Custom invoice number (auto-generated if omitted)
- `due_days` (int): Payment due in N days (default 30)
- `notes` (str): Additional notes for the invoice

### `categorize_expenses`
Automatically categorize business expenses by type (office, travel, marketing, payroll, equipment, software, etc.).

**Parameters:**
- `expenses` (list[dict]): List of dicts with keys: description, amount, date (optional)

### `calculate_vat`
Calculate VAT/tax for any country with support for inclusive/exclusive amounts.

**Parameters:**
- `amount` (float): The monetary amount
- `country_code` (str): ISO country code (default GB)
- `vat_inclusive` (bool): If True, amount already includes VAT
- `custom_rate` (float): Override with a custom VAT rate (e.g. 0.15 for 15%)

### `profit_and_loss`
Generate a profit and loss statement from income and expense records.

**Parameters:**
- `income` (list[dict]): List of dicts with keys: description, amount, date, category
- `expenses` (list[dict]): List of dicts with keys: description, amount, date, category
- `period_start` (str): Start date (YYYY-MM-DD) for filtering
- `period_end` (str): End date (YYYY-MM-DD) for filtering

### `bank_reconciliation`
Reconcile bank statement transactions against book records. Matches by reference or amount+date.

**Parameters:**
- `bank_transactions` (list[dict]): List of dicts with keys: date, description, amount, reference
- `book_transactions` (list[dict]): List of dicts with keys: date, description, amount, reference
- `tolerance` (float): Amount tolerance for matching (default 0.01)

## Authentication

Free tier: 30 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT — MEOK AI Labs
