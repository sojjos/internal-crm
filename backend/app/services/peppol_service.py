"""Peppol/UBL e-invoicing service."""
import os
from datetime import datetime
from typing import TYPE_CHECKING
from lxml import etree

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.company import CompanySettings


# UBL 2.1 namespaces
UBL_NS = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
CAC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
CBC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

NSMAP = {
    None: UBL_NS,
    "cac": CAC_NS,
    "cbc": CBC_NS,
}


def generate_ubl_invoice(invoice: "Invoice", company: "CompanySettings") -> str:
    """Generate UBL 2.1 XML for Peppol e-invoicing.

    Args:
        invoice: Invoice model with lines and client loaded
        company: Company settings

    Returns:
        Path to generated XML file
    """
    # Create root element
    root = etree.Element(
        "{%s}Invoice" % UBL_NS,
        nsmap=NSMAP
    )

    # UBL Version
    etree.SubElement(root, "{%s}UBLVersionID" % CBC_NS).text = "2.1"

    # Customization ID (Peppol BIS 3.0)
    etree.SubElement(
        root, "{%s}CustomizationID" % CBC_NS
    ).text = "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"

    # Profile ID
    etree.SubElement(
        root, "{%s}ProfileID" % CBC_NS
    ).text = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

    # Invoice number
    etree.SubElement(root, "{%s}ID" % CBC_NS).text = invoice.invoice_number

    # Issue date
    etree.SubElement(
        root, "{%s}IssueDate" % CBC_NS
    ).text = invoice.invoice_date.strftime("%Y-%m-%d")

    # Due date
    etree.SubElement(
        root, "{%s}DueDate" % CBC_NS
    ).text = invoice.due_date.strftime("%Y-%m-%d")

    # Invoice type code (380 = Commercial invoice)
    etree.SubElement(root, "{%s}InvoiceTypeCode" % CBC_NS).text = "380"

    # Document currency
    etree.SubElement(root, "{%s}DocumentCurrencyCode" % CBC_NS).text = "EUR"

    # Supplier (AccountingSupplierParty)
    supplier_party = etree.SubElement(root, "{%s}AccountingSupplierParty" % CAC_NS)
    party = etree.SubElement(supplier_party, "{%s}Party" % CAC_NS)

    # Supplier endpoint (Peppol ID)
    if company.peppol_participant_id:
        endpoint = etree.SubElement(party, "{%s}EndpointID" % CBC_NS)
        endpoint.text = company.peppol_participant_id
        endpoint.set("schemeID", "0208")  # Belgian enterprise number

    # Supplier name
    party_name = etree.SubElement(party, "{%s}PartyName" % CAC_NS)
    etree.SubElement(party_name, "{%s}Name" % CBC_NS).text = company.company_name

    # Supplier address
    postal_address = etree.SubElement(party, "{%s}PostalAddress" % CAC_NS)
    if company.address_street:
        etree.SubElement(postal_address, "{%s}StreetName" % CBC_NS).text = company.address_street
    if company.address_city:
        etree.SubElement(postal_address, "{%s}CityName" % CBC_NS).text = company.address_city
    if company.address_postal_code:
        etree.SubElement(postal_address, "{%s}PostalZone" % CBC_NS).text = company.address_postal_code
    country = etree.SubElement(postal_address, "{%s}Country" % CAC_NS)
    etree.SubElement(country, "{%s}IdentificationCode" % CBC_NS).text = "BE"

    # Supplier VAT
    if company.vat_number:
        tax_scheme = etree.SubElement(party, "{%s}PartyTaxScheme" % CAC_NS)
        etree.SubElement(tax_scheme, "{%s}CompanyID" % CBC_NS).text = company.vat_number
        tax_scheme_inner = etree.SubElement(tax_scheme, "{%s}TaxScheme" % CAC_NS)
        etree.SubElement(tax_scheme_inner, "{%s}ID" % CBC_NS).text = "VAT"

    # Customer (AccountingCustomerParty)
    customer_party = etree.SubElement(root, "{%s}AccountingCustomerParty" % CAC_NS)
    party = etree.SubElement(customer_party, "{%s}Party" % CAC_NS)

    # Customer endpoint (Peppol ID)
    if invoice.client.peppol_id:
        endpoint = etree.SubElement(party, "{%s}EndpointID" % CBC_NS)
        endpoint.text = invoice.client.peppol_id
        endpoint.set("schemeID", "0208")

    # Customer name
    party_name = etree.SubElement(party, "{%s}PartyName" % CAC_NS)
    etree.SubElement(party_name, "{%s}Name" % CBC_NS).text = invoice.client.name

    # Customer address
    postal_address = etree.SubElement(party, "{%s}PostalAddress" % CAC_NS)
    if invoice.client.address_street:
        etree.SubElement(postal_address, "{%s}StreetName" % CBC_NS).text = invoice.client.address_street
    if invoice.client.address_city:
        etree.SubElement(postal_address, "{%s}CityName" % CBC_NS).text = invoice.client.address_city
    if invoice.client.address_postal_code:
        etree.SubElement(postal_address, "{%s}PostalZone" % CBC_NS).text = invoice.client.address_postal_code
    country = etree.SubElement(postal_address, "{%s}Country" % CAC_NS)
    etree.SubElement(country, "{%s}IdentificationCode" % CBC_NS).text = "BE"

    # Customer VAT
    if invoice.client.vat_number:
        tax_scheme = etree.SubElement(party, "{%s}PartyTaxScheme" % CAC_NS)
        etree.SubElement(tax_scheme, "{%s}CompanyID" % CBC_NS).text = invoice.client.vat_number
        tax_scheme_inner = etree.SubElement(tax_scheme, "{%s}TaxScheme" % CAC_NS)
        etree.SubElement(tax_scheme_inner, "{%s}ID" % CBC_NS).text = "VAT"

    # Tax total
    tax_total = etree.SubElement(root, "{%s}TaxTotal" % CAC_NS)
    tax_amount = etree.SubElement(tax_total, "{%s}TaxAmount" % CBC_NS)
    tax_amount.text = f"{invoice.total_vat:.2f}"
    tax_amount.set("currencyID", "EUR")

    # Tax subtotal (simplified - assuming single VAT rate)
    tax_subtotal = etree.SubElement(tax_total, "{%s}TaxSubtotal" % CAC_NS)
    taxable_amount = etree.SubElement(tax_subtotal, "{%s}TaxableAmount" % CBC_NS)
    taxable_amount.text = f"{invoice.total_htva:.2f}"
    taxable_amount.set("currencyID", "EUR")
    tax_amount = etree.SubElement(tax_subtotal, "{%s}TaxAmount" % CBC_NS)
    tax_amount.text = f"{invoice.total_vat:.2f}"
    tax_amount.set("currencyID", "EUR")
    tax_category = etree.SubElement(tax_subtotal, "{%s}TaxCategory" % CAC_NS)
    etree.SubElement(tax_category, "{%s}ID" % CBC_NS).text = "S"  # Standard rate
    etree.SubElement(tax_category, "{%s}Percent" % CBC_NS).text = "21"
    tax_scheme = etree.SubElement(tax_category, "{%s}TaxScheme" % CAC_NS)
    etree.SubElement(tax_scheme, "{%s}ID" % CBC_NS).text = "VAT"

    # Legal monetary total
    monetary_total = etree.SubElement(root, "{%s}LegalMonetaryTotal" % CAC_NS)
    line_ext = etree.SubElement(monetary_total, "{%s}LineExtensionAmount" % CBC_NS)
    line_ext.text = f"{invoice.total_htva:.2f}"
    line_ext.set("currencyID", "EUR")
    tax_excl = etree.SubElement(monetary_total, "{%s}TaxExclusiveAmount" % CBC_NS)
    tax_excl.text = f"{invoice.total_htva:.2f}"
    tax_excl.set("currencyID", "EUR")
    tax_incl = etree.SubElement(monetary_total, "{%s}TaxInclusiveAmount" % CBC_NS)
    tax_incl.text = f"{invoice.total_tvac:.2f}"
    tax_incl.set("currencyID", "EUR")
    payable = etree.SubElement(monetary_total, "{%s}PayableAmount" % CBC_NS)
    payable.text = f"{invoice.total_tvac:.2f}"
    payable.set("currencyID", "EUR")

    # Invoice lines
    for line in invoice.lines:
        inv_line = etree.SubElement(root, "{%s}InvoiceLine" % CAC_NS)
        etree.SubElement(inv_line, "{%s}ID" % CBC_NS).text = str(line.line_number)

        qty = etree.SubElement(inv_line, "{%s}InvoicedQuantity" % CBC_NS)
        qty.text = str(line.quantity)
        qty.set("unitCode", line.unit.upper() if line.unit else "C62")

        line_ext = etree.SubElement(inv_line, "{%s}LineExtensionAmount" % CBC_NS)
        line_ext.text = f"{line.line_total_htva:.2f}"
        line_ext.set("currencyID", "EUR")

        # Item
        item = etree.SubElement(inv_line, "{%s}Item" % CAC_NS)
        etree.SubElement(item, "{%s}Description" % CBC_NS).text = line.description
        etree.SubElement(item, "{%s}Name" % CBC_NS).text = line.description[:50]

        # Item tax category
        tax_cat = etree.SubElement(item, "{%s}ClassifiedTaxCategory" % CAC_NS)
        etree.SubElement(tax_cat, "{%s}ID" % CBC_NS).text = "S"
        etree.SubElement(tax_cat, "{%s}Percent" % CBC_NS).text = str(line.vat_rate)
        tax_scheme = etree.SubElement(tax_cat, "{%s}TaxScheme" % CAC_NS)
        etree.SubElement(tax_scheme, "{%s}ID" % CBC_NS).text = "VAT"

        # Price
        price = etree.SubElement(inv_line, "{%s}Price" % CAC_NS)
        price_amount = etree.SubElement(price, "{%s}PriceAmount" % CBC_NS)
        price_amount.text = f"{line.unit_price:.2f}"
        price_amount.set("currencyID", "EUR")

    # Create output directory
    output_dir = os.path.join(settings.UPLOAD_DIR, "invoices", "ubl")
    os.makedirs(output_dir, exist_ok=True)

    # Write XML file
    filename = f"invoice_{invoice.invoice_number.replace('/', '-')}.xml"
    filepath = os.path.join(output_dir, filename)

    tree = etree.ElementTree(root)
    tree.write(filepath, pretty_print=True, xml_declaration=True, encoding="UTF-8")

    return filepath


def send_peppol_invoice(invoice: "Invoice", company: "CompanySettings") -> bool:
    """Send invoice via Peppol network.

    This is a placeholder - actual implementation depends on
    the Peppol Access Point provider being used.

    Args:
        invoice: Invoice model
        company: Company settings with Peppol config

    Returns:
        True if sent successfully
    """
    if not company.peppol_enabled:
        raise ValueError("Peppol is not enabled")

    if not invoice.ubl_path or not os.path.exists(invoice.ubl_path):
        raise ValueError("UBL file not generated")

    # TODO: Implement actual Peppol sending via Access Point API
    # This depends on the specific Access Point provider (e.g., Storecove, Unifiedpost, etc.)

    # Placeholder - in production, this would:
    # 1. Connect to Peppol Access Point API
    # 2. Upload the UBL XML document
    # 3. Handle response and errors

    print(f"Would send Peppol invoice {invoice.invoice_number} to {invoice.client.peppol_id}")

    return True
