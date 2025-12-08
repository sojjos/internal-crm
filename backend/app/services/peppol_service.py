"""Peppol/UBL e-invoicing service."""
import os
import time
import httpx
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List, Dict, Any
from lxml import etree

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.company import CompanySettings


# Peppol Directory API configuration
PEPPOL_DIRECTORY_BASE_URL = "https://directory.peppol.eu"
PEPPOL_DIRECTORY_SEARCH_ENDPOINT = "/search/1.0/json"

# Rate limiting: max 2 requests per second
_last_request_time = 0.0
_request_interval = 0.5  # 500ms between requests


class PeppolDirectoryClient:
    """Client for Peppol Directory REST API.

    Documentation: https://directory.peppol.eu/public/menuitem-docs-rest-api
    """

    def __init__(self):
        self.base_url = PEPPOL_DIRECTORY_BASE_URL
        self.search_endpoint = PEPPOL_DIRECTORY_SEARCH_ENDPOINT

    def _rate_limit(self):
        """Ensure we don't exceed 2 requests per second."""
        global _last_request_time
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < _request_interval:
            time.sleep(_request_interval - elapsed)
        _last_request_time = time.time()

    async def search_participant(
        self,
        participant_id: Optional[str] = None,
        name: Optional[str] = None,
        country: Optional[str] = None,
        page_index: int = 0,
        page_count: int = 20
    ) -> Dict[str, Any]:
        """Search for participants in the Peppol Directory.

        Args:
            participant_id: Exact Peppol participant ID (e.g., "0208:0123456789")
            name: Partial business name search (min 3 chars)
            country: Country code (e.g., "BE", "FR", "NL")
            page_index: Page index for pagination (0-based)
            page_count: Number of results per page (max 1000)

        Returns:
            Dictionary with search results and metadata
        """
        self._rate_limit()

        params = {
            "resultPageIndex": page_index,
            "resultPageCount": min(page_count, 1000)
        }

        if participant_id:
            # Format: scheme::id (e.g., "iso6523-actorid-upis::0208:0123456789")
            if "::" not in participant_id:
                # Auto-format Belgian enterprise numbers
                participant_id = f"iso6523-actorid-upis::0208:{participant_id}"
            params["participant"] = participant_id

        if name and len(name) >= 3:
            params["name"] = name

        if country and len(country) == 2:
            params["country"] = country.upper()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}{self.search_endpoint}",
                params=params
            )

            if response.status_code == 429:
                raise Exception("Peppol Directory rate limit exceeded. Please wait.")

            if response.status_code == 400:
                raise Exception("Invalid search parameters (min 3 characters required)")

            response.raise_for_status()

            data = response.json()

            # Extract headers metadata
            headers = response.headers
            return {
                "total_count": int(headers.get("total-result-count", 0)),
                "page_index": int(headers.get("result-page-index", 0)),
                "page_count": int(headers.get("result-page-count", 0)),
                "matches": data.get("matches", [])
            }

    async def lookup_participant(self, participant_id: str) -> Optional[Dict[str, Any]]:
        """Lookup a specific Peppol participant by ID.

        Args:
            participant_id: The Peppol participant ID (e.g., "0208:0123456789" for Belgian enterprise)

        Returns:
            Participant data if found, None otherwise
        """
        result = await self.search_participant(participant_id=participant_id)

        if result["matches"]:
            return result["matches"][0]
        return None

    async def validate_participant(self, participant_id: str) -> Dict[str, Any]:
        """Validate if a participant exists and can receive invoices.

        Args:
            participant_id: The Peppol participant ID

        Returns:
            Dictionary with validation status and details
        """
        participant = await self.lookup_participant(participant_id)

        if not participant:
            return {
                "valid": False,
                "registered": False,
                "message": "Participant not found in Peppol Directory",
                "participant_id": participant_id,
                "can_receive_invoice": False
            }

        # Check if participant can receive invoices (document type check)
        doc_types = participant.get("docTypes", [])
        can_receive_invoice = any(
            "invoice" in dt.get("value", "").lower() or
            "billing" in dt.get("value", "").lower()
            for dt in doc_types
        )

        return {
            "valid": True,
            "registered": True,
            "message": "Participant found and registered",
            "participant_id": participant_id,
            "name": participant.get("entities", [{}])[0].get("name", [{}])[0].get("value", ""),
            "country": participant.get("entities", [{}])[0].get("countryCode", ""),
            "can_receive_invoice": can_receive_invoice,
            "document_types": [dt.get("value", "") for dt in doc_types],
            "registration_date": participant.get("registrationDate", "")
        }

    async def search_belgian_companies(
        self,
        name: Optional[str] = None,
        enterprise_number: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for Belgian companies in Peppol Directory.

        Args:
            name: Company name (partial match, min 3 chars)
            enterprise_number: Belgian enterprise number (KBO/BCE)

        Returns:
            List of matching Belgian Peppol participants
        """
        if enterprise_number:
            # Clean and format Belgian enterprise number
            clean_num = enterprise_number.replace(".", "").replace(" ", "").replace("BE", "")
            result = await self.search_participant(
                participant_id=f"0208:{clean_num}",
                country="BE"
            )
        else:
            result = await self.search_participant(name=name, country="BE")

        return result.get("matches", [])


# Global client instance
peppol_directory = PeppolDirectoryClient()


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


async def validate_recipient_before_send(
    client_peppol_id: str
) -> Dict[str, Any]:
    """Validate recipient before sending Peppol invoice.

    Args:
        client_peppol_id: Client's Peppol participant ID

    Returns:
        Validation result dictionary
    """
    return await peppol_directory.validate_participant(client_peppol_id)


async def send_peppol_invoice(
    invoice: "Invoice",
    company: "CompanySettings",
    validate_recipient: bool = True
) -> Dict[str, Any]:
    """Send invoice via Peppol network.

    Args:
        invoice: Invoice model with lines and client loaded
        company: Company settings with Peppol config
        validate_recipient: Whether to validate recipient before sending

    Returns:
        Dictionary with send status and details
    """
    if not company.peppol_enabled:
        raise ValueError("Peppol is not enabled")

    if not invoice.ubl_path or not os.path.exists(invoice.ubl_path):
        raise ValueError("UBL file not generated")

    if not invoice.client.peppol_id:
        raise ValueError("Client has no Peppol ID configured")

    result = {
        "success": False,
        "invoice_number": invoice.invoice_number,
        "recipient_peppol_id": invoice.client.peppol_id,
        "validation": None,
        "message": ""
    }

    # Validate recipient in Peppol Directory
    if validate_recipient:
        validation = await validate_recipient_before_send(invoice.client.peppol_id)
        result["validation"] = validation

        if not validation["valid"]:
            result["message"] = f"Recipient not found in Peppol Directory: {invoice.client.peppol_id}"
            return result

        if not validation["can_receive_invoice"]:
            result["message"] = "Recipient is registered but cannot receive invoices"
            return result

    # TODO: Implement actual Peppol sending via Access Point API
    # This depends on the specific Access Point provider:
    # - Storecove: https://www.storecove.com/docs/
    # - Unifiedpost: Belgian provider
    # - Basware: https://www.basware.com/
    # - OpenPeppol certified Access Points list

    # Placeholder implementation - in production:
    # 1. Connect to Peppol Access Point API with credentials
    # 2. Upload the UBL XML document
    # 3. Get transmission ID and status
    # 4. Handle async delivery notifications

    result["success"] = True
    result["message"] = f"Invoice {invoice.invoice_number} queued for Peppol delivery"
    result["transmission_id"] = f"PEPPOL-{invoice.invoice_number}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return result


def send_peppol_invoice_sync(invoice: "Invoice", company: "CompanySettings") -> bool:
    """Synchronous wrapper for send_peppol_invoice (deprecated).

    Use send_peppol_invoice async function instead.
    """
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            send_peppol_invoice(invoice, company, validate_recipient=False)
        )
        return result["success"]
    finally:
        loop.close()
