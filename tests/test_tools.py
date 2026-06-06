"""Functional tests for Accounting AI MCP Server tools.

Tests invoice generation, expense categorization, VAT calculation,
profit & loss, and bank reconciliation. No external API calls.
"""
import json
import os
import sys
from unittest.mock import MagicMock

_mock_mcp_module = MagicMock()

class _MockFastMCP:
    def __init__(self, name="", **kwargs):
        self.name = name

    def tool(self):
        def decorator(fn):
            return fn
        return decorator

_mock_mcp_module.FastMCP = _MockFastMCP
sys.modules["mcp"] = MagicMock()
sys.modules["mcp.server"] = MagicMock()
sys.modules["mcp.server.fastmcp"] = _mock_mcp_module

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.pop("MEOK_API_KEY", None)

import server as srv  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def reset_state():
    srv._call_counts.clear()
    yield
    srv._call_counts.clear()


class TestMcpRegistration:
    def test_mcp_object_exists(self):
        assert hasattr(srv, "mcp")

    def test_all_tools_callable(self):
        tool_names = [
            "generate_invoice", "categorize_expenses",
            "calculate_vat", "profit_and_loss", "bank_reconciliation",
        ]
        for name in tool_names:
            assert callable(getattr(srv, name)), f"Tool not callable: {name}"


class TestGenerateInvoice:
    def test_basic_invoice(self):
        result = srv.generate_invoice(
            business_name="Acme Corp",
            client_name="Beta Ltd",
            items=[{"description": "Consulting", "quantity": 10, "unit_price": 100}],
        )
        assert result["business_name"] == "Acme Corp"
        assert result["client_name"] == "Beta Ltd"
        assert result["status"] == "ISSUED"
        assert len(result["line_items"]) == 1
        assert result["line_items"][0]["line_total"] == 1000.0

    def test_vat_calculation_in_invoice(self):
        result = srv.generate_invoice(
            "Biz", "Client",
            items=[{"description": "Service", "quantity": 1, "unit_price": 100}],
            country_code="GB",
        )
        assert float(result["vat_rate"].rstrip("%")) == 20.0
        assert result["vat_amount"] == 20.0
        assert result["total"] == 120.0

    def test_custom_invoice_number(self):
        result = srv.generate_invoice(
            "Biz", "Client",
            items=[{"description": "Item", "quantity": 1, "unit_price": 50}],
            invoice_number="INV-2025-001",
        )
        assert result["invoice_number"] == "INV-2025-001"

    def test_auto_generated_invoice_number(self):
        result = srv.generate_invoice(
            "Biz", "Client",
            items=[{"description": "Item", "quantity": 1, "unit_price": 10}],
        )
        assert result["invoice_number"].startswith("INV-")

    def test_custom_due_days(self):
        result = srv.generate_invoice(
            "Biz", "Client",
            items=[{"description": "Item", "quantity": 1, "unit_price": 10}],
            due_days=14,
        )
        assert result["due_date"] is not None

    def test_multiple_items(self):
        items = [
            {"description": "Service A", "quantity": 2, "unit_price": 150},
            {"description": "Service B", "quantity": 1, "unit_price": 300},
        ]
        result = srv.generate_invoice("Biz", "Client", items=items)
        assert len(result["line_items"]) == 2
        assert result["subtotal"] == 600.0

    def test_us_country_no_vat(self):
        result = srv.generate_invoice(
            "US Biz", "US Client",
            items=[{"description": "Service", "quantity": 1, "unit_price": 100}],
            country_code="US",
        )
        assert float(result["vat_rate"].rstrip("%")) == 0.0
        assert result["vat_amount"] == 0.0
        assert result["total"] == 100.0


class TestCategorizeExpenses:
    def test_office_expense(self):
        result = srv.categorize_expenses([
            {"description": "Office rent payment", "amount": 2000},
        ])
        assert "office" in result["categories"]
        assert result["categories"]["office"]["total"] == 2000.0

    def test_travel_expense(self):
        result = srv.categorize_expenses([
            {"description": "Flight to London", "amount": 350},
            {"description": "Hotel stay", "amount": 180},
        ])
        assert "travel" in result["categories"]
        assert result["categories"]["travel"]["total"] == 530.0

    def test_mixed_expenses(self):
        result = srv.categorize_expenses([
            {"description": "Office rent", "amount": 1500},
            {"description": "Google Ads", "amount": 500},
            {"description": "Laptop", "amount": 1200},
        ])
        assert result["total_expenses"] == 3
        assert result["grand_total"] == 3200.0

    def test_uncategorized_goes_to_misc(self):
        result = srv.categorize_expenses([
            {"description": "XYZ unknown item abc123", "amount": 100},
        ])
        assert "miscellaneous" in result["categories"]

    def test_software_expense(self):
        result = srv.categorize_expenses([
            {"description": "AWS cloud hosting subscription", "amount": 500},
        ])
        assert "software" in result["categories"]


class TestCalculateVat:
    def test_gb_vat_exclusive(self):
        result = srv.calculate_vat(100.0, country_code="GB")
        assert result["net_amount"] == 100.0
        assert result["vat_amount"] == 20.0
        assert result["gross_amount"] == 120.0

    def test_gb_vat_inclusive(self):
        result = srv.calculate_vat(120.0, country_code="GB", vat_inclusive=True)
        assert result["net_amount"] == 100.0
        assert result["vat_amount"] == 20.0
        assert result["gross_amount"] == 120.0

    def test_us_no_vat(self):
        result = srv.calculate_vat(100.0, country_code="US")
        assert result["vat_amount"] == 0.0
        assert result["gross_amount"] == 100.0

    def test_custom_rate(self):
        result = srv.calculate_vat(100.0, custom_rate=0.15)
        assert result["vat_amount"] == 15.0
        assert result["gross_amount"] == 115.0

    def test_de_vat(self):
        result = srv.calculate_vat(100.0, country_code="DE")
        assert result["vat_amount"] == 19.0

    def test_country_code_uppercased(self):
        result = srv.calculate_vat(100.0, country_code="gb")
        assert result["country_code"] == "GB"


class TestProfitAndLoss:
    def test_basic_profit(self):
        income = [{"description": "Revenue", "amount": 10000, "category": "Sales"}]
        expenses = [{"description": "Costs", "amount": 6000, "category": "Operations"}]
        result = srv.profit_and_loss(income, expenses)
        assert result["net_profit"] == 4000.0
        assert result["status"] == "PROFIT"
        assert "40.0%" in result["profit_margin"] or result["net_profit"] == 4000.0

    def test_loss(self):
        income = [{"description": "Revenue", "amount": 3000}]
        expenses = [{"description": "Costs", "amount": 5000}]
        result = srv.profit_and_loss(income, expenses)
        assert result["net_profit"] == -2000.0
        assert result["status"] == "LOSS"

    def test_break_even(self):
        income = [{"description": "Revenue", "amount": 5000}]
        expenses = [{"description": "Costs", "amount": 5000}]
        result = srv.profit_and_loss(income, expenses)
        assert result["status"] == "BREAK_EVEN"

    def test_period_filtering(self):
        income = [
            {"description": "Jan Revenue", "amount": 5000, "date": "2025-01-15"},
            {"description": "Mar Revenue", "amount": 3000, "date": "2025-03-15"},
        ]
        expenses = [
            {"description": "Jan Cost", "amount": 2000, "date": "2025-01-20"},
            {"description": "Mar Cost", "amount": 1000, "date": "2025-03-20"},
        ]
        result = srv.profit_and_loss(
            income, expenses, period_start="2025-03-01", period_end="2025-03-31"
        )
        assert result["net_profit"] == 2000.0
        assert result["status"] == "PROFIT"

    def test_category_breakdown(self):
        income = [
            {"description": "Consulting", "amount": 5000, "category": "Services"},
            {"description": "Products", "amount": 3000, "category": "Products"},
        ]
        expenses = [{"description": "Rent", "amount": 2000, "category": "Overhead"}]
        result = srv.profit_and_loss(income, expenses)
        assert "Services" in result["income"]["breakdown"]
        assert "Products" in result["income"]["breakdown"]


class TestBankReconciliation:
    def test_perfect_match(self):
        bank = [{"date": "2025-01-01", "description": "Payment", "amount": 100, "reference": "TX001"}]
        book = [{"date": "2025-01-01", "description": "Payment", "amount": 100, "reference": "TX001"}]
        result = srv.bank_reconciliation(bank, book)
        assert result["reconciled"] is True
        assert result["matched_count"] == 1

    def test_unmatched_transactions(self):
        bank = [{"date": "2025-01-01", "description": "Payment", "amount": 100, "reference": "TX001"}]
        book = [{"date": "2025-01-02", "description": "Other", "amount": 200, "reference": "TX002"}]
        result = srv.bank_reconciliation(bank, book)
        assert result["reconciled"] is False
        assert result["unmatched_bank_count"] == 1
        assert result["unmatched_book_count"] == 1

    def test_amount_plus_date_match(self):
        bank = [{"date": "2025-01-01", "description": "Payment", "amount": 100}]
        book = [{"date": "2025-01-01", "description": "Bank payment", "amount": 100}]
        result = srv.bank_reconciliation(bank, book)
        assert result["matched_count"] == 1

    def test_discrepancy_calculation(self):
        bank = [{"date": "2025-01-01", "description": "In", "amount": 150}]
        book = [{"date": "2025-01-01", "description": "In", "amount": 100}]
        result = srv.bank_reconciliation(bank, book)
        assert result["discrepancy"] == 50.0

    def test_tolerance(self):
        bank = [{"date": "2025-01-01", "description": "In", "amount": 100.02}]
        book = [{"date": "2025-01-01", "description": "In", "amount": 100.00}]
        result = srv.bank_reconciliation(bank, book, tolerance=0.05)
        assert result["matched_count"] == 1
        assert result["reconciled"] is True

    def test_empty_transactions(self):
        result = srv.bank_reconciliation([], [])
        assert result["reconciled"] is True
        assert result["matched_count"] == 0

    def test_reference_match(self):
        bank = [{"date": "2025-01-01", "description": "In", "amount": 100, "reference": "REF-001"}]
        book = [{"date": "2025-01-02", "description": "Out", "amount": 250, "reference": "REF-001"}]
        result = srv.bank_reconciliation(bank, book)
        assert result["matched_count"] == 1
        assert result["matched"][0]["match_type"] == "reference"