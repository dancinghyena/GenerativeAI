"""Invoice and employee tools for the Chinook store."""

from langchain_core.tools import tool

from db import run_query


@tool
def get_invoices_by_customer_sorted_by_date(customer_id: str) -> str:
    """Retrieve all invoices for a customer, sorted by invoice date (most recent first)."""
    safe = str(customer_id).replace("'", "''")
    return run_query(
        f"""
        SELECT InvoiceId, InvoiceDate, Total, BillingCity, BillingCountry
        FROM Invoice
        WHERE CustomerId = {int(safe) if str(safe).isdigit() else 0}
        ORDER BY InvoiceDate DESC;
        """
    )


@tool
def get_invoices_sorted_by_unit_price(customer_id: str) -> str:
    """Retrieve invoice line items for a customer, sorted by unit price (highest to lowest)."""
    safe = str(customer_id).replace("'", "''")
    cid = int(safe) if str(safe).isdigit() else 0
    return run_query(
        f"""
        SELECT Invoice.InvoiceId, Invoice.InvoiceDate, Track.Name AS Track,
               InvoiceLine.UnitPrice, InvoiceLine.Quantity, Invoice.Total
        FROM Invoice
        JOIN InvoiceLine ON Invoice.InvoiceId = InvoiceLine.InvoiceId
        JOIN Track ON InvoiceLine.TrackId = Track.TrackId
        WHERE Invoice.CustomerId = {cid}
        ORDER BY InvoiceLine.UnitPrice DESC
        LIMIT 30;
        """
    )


@tool
def get_employee_by_invoice_and_customer(invoice_id: str, customer_id: str) -> str:
    """Retrieve the support employee associated with a specific invoice and customer."""
    inv = int(invoice_id) if str(invoice_id).isdigit() else 0
    cid = int(customer_id) if str(customer_id).isdigit() else 0
    return run_query(
        f"""
        SELECT Employee.EmployeeId, Employee.FirstName, Employee.LastName,
               Employee.Title, Employee.Email, Invoice.InvoiceId, Invoice.Total
        FROM Invoice
        JOIN Customer ON Invoice.CustomerId = Customer.CustomerId
        JOIN Employee ON Customer.SupportRepId = Employee.EmployeeId
        WHERE Invoice.InvoiceId = {inv} AND Customer.CustomerId = {cid};
        """
    )


INVOICE_TOOLS = [
    get_invoices_by_customer_sorted_by_date,
    get_invoices_sorted_by_unit_price,
    get_employee_by_invoice_and_customer,
]
