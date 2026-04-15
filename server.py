"""
Accounting AI MCP Server
Small business accounting tools powered by MEOK AI Labs.
"""


import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import json
import time
import hashlib
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("accounting-ai", instructions="MEOK AI Labs MCP Server")

# --- Rate Limiting ---
_call_counts: dict[str, list[float]] = defaultdict(list)
FREE_TIER_LIMIT = 30
WINDOW = 86400  # 24 hours


def _check_rate_limit(tool_name: str) -> None:
    now = time.time()
    _call_counts[tool_name] = [t for t in _call_counts[tool_name] if now - t < WINDOW]
    if len(_call_counts[tool_name]) >= FREE_TIER_LIMIT:
        raise ValueError(
            f"Rate limit exceeded for {tool_name}. Free tier: {FREE_TIER_LIMIT} calls/day. "
            "Upgrade at https://meok.ai/pricing"
        )
    _call_counts[tool_name].append(now)


# --- VAT Rates by Country ---
VAT_RATES = {
    "GB": 0.20, "DE": 0.19, "FR": 0.20, "IT": 0.22, "ES": 0.21,
    "NL": 0.21, "BE": 0.21, "AT": 0.20, "SE": 0.25, "DK": 0.25,
    "FI": 0.24, "PT": 0.23, "IE": 0.23, "PL": 0.23, "CZ": 0.21,
    "AU": 0.10, "NZ": 0.15, "CA": 0.05, "JP": 0.10, "IN": 0.18,
    "US": 0.00,  # No federal VAT
}

# --- Expense Categories ---
EXPENSE_CATEGORIES = {
    "office": ["rent", "lease", "utilities", "electricity", "water", "internet", "phone", "cleaning"],
    "travel": ["flight", "hotel", "taxi", "uber", "train", "fuel", "petrol", "gas", "parking", "toll"],
    "marketing": ["advertising", "ads", "google ads", "facebook", "social media", "seo", "branding", "print"],
    "payroll": ["salary", "wages", "bonus", "pension", "insurance", "benefits", "payroll"],
    "equipment": ["computer", "laptop", "monitor", "printer", "furniture", "desk", "chair", "hardware"],
    "software": ["subscription", "saas", "license", "cloud", "hosting", "domain", "aws", "azure"],
    "professional": ["legal", "lawyer", "accountant", "consultant", "audit", "advisory"],
    "supplies": ["stationery", "paper", "ink", "toner", "postage", "shipping", "packaging"],
    "meals": ["lunch", "dinner", "catering", "coffee", "restaurant", "food"],
    "miscellaneous": [],
}


@mcp.tool()
def generate_invoice(
    business_name: str,
    client_name: str,
    items: list[dict],
    currency: str = "GBP",
    country_code: str = "GB",
    invoice_number: str | None = None,
    due_days: int = 30,
    notes: str = "", api_key: str = "") -> dict:
    """Generate a professional invoice with line items, VAT, and totals.

    Args:
        business_name: Your business/company name
        client_name: Client or customer name
        items: List of dicts with keys: description, quantity, unit_price
        currency: Currency code (GBP, USD, EUR, etc.)
        country_code: ISO country code for VAT rate
        invoice_number: Custom invoice number (auto-generated if omitted)
        due_days: Payment due in N days (default 30)
        notes: Additional notes for the invoice
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("generate_invoice")

    vat_rate = VAT_RATES.get(country_code.upper(), 0.20)
    today = date.today()
    due_date = date.fromordinal(today.toordinal() + due_days)

    if not invoice_number:
        hash_input = f"{business_name}{client_name}{today.isoformat()}{time.time()}"
        invoice_number = "INV-" + hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()

    line_items = []
    subtotal = Decimal("0")

    for item in items:
        desc = item.get("description", "Item")
        qty = Decimal(str(item.get("quantity", 1)))
        price = Decimal(str(item.get("unit_price", 0)))
        line_total = (qty * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal += line_total
        line_items.append({
            "description": desc,
            "quantity": float(qty),
            "unit_price": float(price),
            "line_total": float(line_total),
        })

    vat_amount = (subtotal * Decimal(str(vat_rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = subtotal + vat_amount

    return {
        "invoice_number": invoice_number,
        "business_name": business_name,
        "client_name": client_name,
        "issue_date": today.isoformat(),
        "due_date": due_date.isoformat(),
        "currency": currency.upper(),
        "line_items": line_items,
        "subtotal": float(subtotal),
        "vat_rate": f"{vat_rate * 100:.1f}%",
        "vat_amount": float(vat_amount),
        "total": float(total),
        "country_code": country_code.upper(),
        "notes": notes,
        "status": "ISSUED",
    }


@mcp.tool()
def categorize_expenses(expenses: list[dict], api_key: str = "") -> dict:
    """Automatically categorize business expenses by type.

    Args:
        expenses: List of dicts with keys: description, amount, date (optional)
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("categorize_expenses")

    categorized = defaultdict(lambda: {"items": [], "total": 0.0})
    uncategorized = []

    for expense in expenses:
        desc = expense.get("description", "").lower()
        amount = float(expense.get("amount", 0))
        exp_date = expense.get("date", date.today().isoformat())
        matched = False

        for category, keywords in EXPENSE_CATEGORIES.items():
            if any(kw in desc for kw in keywords):
                categorized[category]["items"].append({
                    "description": expense.get("description", ""),
                    "amount": amount,
                    "date": exp_date,
                })
                categorized[category]["total"] += amount
                matched = True
                break

        if not matched:
            categorized["miscellaneous"]["items"].append({
                "description": expense.get("description", ""),
                "amount": amount,
                "date": exp_date,
            })
            categorized["miscellaneous"]["total"] += amount

    grand_total = sum(c["total"] for c in categorized.values())

    summary = {}
    for cat, data in sorted(categorized.items(), key=lambda x: -x[1]["total"]):
        data["total"] = round(data["total"], 2)
        data["percentage"] = round((data["total"] / grand_total * 100) if grand_total else 0, 1)
        data["count"] = len(data["items"])
        summary[cat] = data

    return {
        "categories": summary,
        "grand_total": round(grand_total, 2),
        "total_expenses": len(expenses),
        "category_count": len(summary),
    }


@mcp.tool()
def calculate_vat(
    amount: float,
    country_code: str = "GB",
    vat_inclusive: bool = False,
    custom_rate: float | None = None, api_key: str = "") -> dict:
    """Calculate VAT/tax for any country with support for inclusive/exclusive amounts.

    Args:
        amount: The monetary amount
        country_code: ISO country code (default GB)
        vat_inclusive: If True, amount already includes VAT
        custom_rate: Override with a custom VAT rate (e.g. 0.15 for 15%)
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("calculate_vat")

    rate = custom_rate if custom_rate is not None else VAT_RATES.get(country_code.upper(), 0.20)
    amt = Decimal(str(amount))

    if vat_inclusive:
        net = (amt / (1 + Decimal(str(rate)))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        vat = amt - net
        gross = amt
    else:
        net = amt
        vat = (amt * Decimal(str(rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gross = net + vat

    return {
        "net_amount": float(net),
        "vat_rate": f"{rate * 100:.1f}%",
        "vat_amount": float(vat),
        "gross_amount": float(gross),
        "country_code": country_code.upper(),
        "vat_inclusive_input": vat_inclusive,
    }


@mcp.tool()
def profit_and_loss(
    income: list[dict],
    expenses: list[dict],
    period_start: str = "",
    period_end: str = "", api_key: str = "") -> dict:
    """Generate a profit and loss statement from income and expense records.

    Args:
        income: List of dicts with keys: description, amount, date (optional), category (optional)
        expenses: List of dicts with keys: description, amount, date (optional), category (optional)
        period_start: Start date (YYYY-MM-DD) for filtering (optional)
        period_end: End date (YYYY-MM-DD) for filtering (optional)
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("profit_and_loss")

    def filter_by_period(records):
        if not period_start and not period_end:
            return records
        filtered = []
        for r in records:
            d = r.get("date", "")
            if period_start and d < period_start:
                continue
            if period_end and d > period_end:
                continue
            filtered.append(r)
        return filtered

    filtered_income = filter_by_period(income)
    filtered_expenses = filter_by_period(expenses)

    income_by_cat = defaultdict(float)
    for item in filtered_income:
        cat = item.get("category", "Revenue")
        income_by_cat[cat] += float(item.get("amount", 0))

    expense_by_cat = defaultdict(float)
    for item in filtered_expenses:
        cat = item.get("category", "General")
        expense_by_cat[cat] += float(item.get("amount", 0))

    total_income = sum(income_by_cat.values())
    total_expenses = sum(expense_by_cat.values())
    net_profit = total_income - total_expenses
    margin = (net_profit / total_income * 100) if total_income > 0 else 0

    return {
        "period": {
            "start": period_start or "all time",
            "end": period_end or "all time",
        },
        "income": {
            "breakdown": {k: round(v, 2) for k, v in sorted(income_by_cat.items(), key=lambda x: -x[1])},
            "total": round(total_income, 2),
        },
        "expenses": {
            "breakdown": {k: round(v, 2) for k, v in sorted(expense_by_cat.items(), key=lambda x: -x[1])},
            "total": round(total_expenses, 2),
        },
        "net_profit": round(net_profit, 2),
        "profit_margin": f"{margin:.1f}%",
        "status": "PROFIT" if net_profit > 0 else "LOSS" if net_profit < 0 else "BREAK_EVEN",
    }


@mcp.tool()
def bank_reconciliation(
    bank_transactions: list[dict],
    book_transactions: list[dict],
    tolerance: float = 0.01, api_key: str = "") -> dict:
    """Reconcile bank statement transactions against book records.

    Args:
        bank_transactions: List of dicts with keys: date, description, amount, reference (optional)
        book_transactions: List of dicts with keys: date, description, amount, reference (optional)
        tolerance: Amount tolerance for matching (default 0.01)
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("bank_reconciliation")

    matched = []
    unmatched_bank = list(range(len(bank_transactions)))
    unmatched_book = list(range(len(book_transactions)))

    # Match by reference first, then by amount+date
    for bi in list(unmatched_bank):
        bt = bank_transactions[bi]
        bt_ref = bt.get("reference", "").strip().lower()
        bt_amt = float(bt.get("amount", 0))
        bt_date = bt.get("date", "")

        for bki in list(unmatched_book):
            bkt = book_transactions[bki]
            bkt_ref = bkt.get("reference", "").strip().lower()
            bkt_amt = float(bkt.get("amount", 0))
            bkt_date = bkt.get("date", "")

            ref_match = bt_ref and bkt_ref and bt_ref == bkt_ref
            amt_match = abs(bt_amt - bkt_amt) <= tolerance
            date_match = bt_date == bkt_date

            if ref_match or (amt_match and date_match):
                matched.append({
                    "bank": bt,
                    "book": bkt,
                    "match_type": "reference" if ref_match else "amount+date",
                    "difference": round(bt_amt - bkt_amt, 2),
                })
                unmatched_bank.remove(bi)
                unmatched_book.remove(bki)
                break

    bank_total = sum(float(bank_transactions[i].get("amount", 0)) for i in range(len(bank_transactions)))
    book_total = sum(float(book_transactions[i].get("amount", 0)) for i in range(len(book_transactions)))

    return {
        "matched": matched,
        "matched_count": len(matched),
        "unmatched_bank": [bank_transactions[i] for i in unmatched_bank],
        "unmatched_book": [book_transactions[i] for i in unmatched_book],
        "unmatched_bank_count": len(unmatched_bank),
        "unmatched_book_count": len(unmatched_book),
        "bank_balance": round(bank_total, 2),
        "book_balance": round(book_total, 2),
        "discrepancy": round(bank_total - book_total, 2),
        "reconciled": len(unmatched_bank) == 0 and len(unmatched_book) == 0,
    }


if __name__ == "__main__":
    mcp.run()
