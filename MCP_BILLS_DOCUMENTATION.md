# MCP Bills Implementation Documentation

## Overview
The `mcp_bills` module provides a FastMCP server for managing bills/invoices (payment plans) in the yacchi-mcp system. It includes comprehensive functionality for searching and creating bills with detailed validation.

## Features Implemented

### 1. Search Bills (`search_bills`)
**Description**: Query invoice lists by project and customer with flexible filtering options.

**Parameters**:
- `project_ids`: List of project IDs (supports list, JSON string, or CSV format)
- `customer_ids`: List of customer IDs (supports list, JSON string, or CSV format)
- `created_at_from`: Filter by creation date from (ISO 8601 format)
- `created_at_to`: Filter by creation date to (ISO 8601 format)
- `order_by`: Sort field (default: "created_at") - options: created_at, amount, project_id, customer_id
- `order_dir`: Sort direction - "asc" or "desc" (default: "desc")

**Returns**:
```json
{
  "total": 100,
  "returned": 5,
  "order_by": "created_at",
  "order_dir": "desc",
  "items": [
    {
      "bill_number": "PP00000001",
      "created_at": "2026-01-14T00:00:00",
      "tax": 1000.0,
      "amount": 10000.0,
      "project_number": "PROJ-001",
      "project_name": "Project Name",
      "customer_id": "CUST001",
      "project_id": "PROJ001",
      "customer_name": "Customer Name",
      "expected_date_of_payment": "2026-01-30"
    }
  ]
}
```

**Features**:
- Returns up to 5 rows per query
- Requires at least one filter to prevent full table scans
- Supports flexible input formats (list, JSON array string, CSV string)
- Safe SQL parameter binding to prevent SQL injection
- Filters out soft-deleted records (is_deleted = false)

### 2. Create Bill (`create_bill`)
**Description**: Create a new payment plan (bill) with detailed line items.

**Parameters**:
- `information_create_invoice`: BillCreateInfo object containing:
  - `id`: Bill ID (optional, auto-generated if not provided)
  - `customer_id`: Customer ID (required, validated against DB)
  - `payer_code`: Payer code (required, validated against DB)
  - `project_id`: Project ID (required, validated against DB)
  - `payment_date`: Payment date in YYYY-MM-DD format (optional)
  - `expected_date_of_payment`: Expected payment date in YYYY-MM-DD format (optional)
  - `execution_team`: Team or department executing the project (optional)
  - `details`: List of BillDetailsInfo objects (required, non-empty)

**BillDetailsInfo Structure**:
```json
{
  "attribute": "Installation work",
  "product": "Product A",
  "quantity": 5,
  "tax_amount": 1000.0,
  "amount": 10000
}
```

**Validation**:
- Customer ID, payer code, and project ID are validated against the database
- Dates must be in ISO 8601 format (YYYY-MM-DD)
- Details list must not be empty
- Quantity must be greater than 0
- Amount must be non-negative

**Returns**:
```json
{
  "bill_id": "PP00000123",
  "customer_id": "CUST001",
  "project_id": "PROJ001",
  "amount": 10000.0,
  "tax": 1000.0,
  "details_created": 1,
  "details": [
    {
      "id": 1,
      "attribute": "Installation work",
      "product": "Product A",
      "quantity": 5,
      "tax": 1000.0,
      "amount": 10000.0
    }
  ]
}
```

**Features**:
- Automatic bill ID generation using PostgreSQL sequence
- Transaction-safe (rollback on error)
- Automatic calculation of total amount and tax from detail items
- Creates both PaymentPlan and PaymentPlanDetail records in one transaction

### 3. Create Bill Prompt (`bills_create_prompt`)
**Description**: A prompt helper that provides guidance for bill creation.

**Purpose**: Ensures users confirm all required information before creating a bill.

## Database Schema

### PaymentPlan Table
- `id`: String(15) - Primary key, auto-generated (PP00000001, PP00000002, etc.)
- `project_id`: String(15) - Foreign key to projects
- `customer_id`: String(15) - Foreign key to customers
- `payer_code`: String(25) - Payer identifier
- `execution_team`: String(255) - Executing team
- `execution_date`: Date - Expected execution date
- `amount`: Numeric(10,2) - Total amount before tax
- `tax`: Numeric(10,2) - Total tax amount
- `created_at`: Timestamp - Record creation time
- `is_deleted`: Boolean - Soft delete flag

### PaymentPlanDetail Table
- `id`: BigInteger - Primary key, auto-increment
- `payment_plan_id`: String(15) - Foreign key to payment_plans
- `attribute`: String(255) - Item description
- `product`: String(255) - Product/service name
- `quantity`: SmallInteger - Quantity of items
- `amount`: Numeric(12,2) - Amount before tax
- `tax_amount`: Numeric(12,2) - Tax amount
- `created_at`: Timestamp - Record creation time

## Helper Functions

### `_to_jsonable(v)`
Converts non-JSON-serializable types to JSON-safe formats:
- datetime/date/time → ISO 8601 string
- Decimal → float
- UUID → string
- Enum → enum value

### `_rows_to_dicts(rows)`
Converts SQLAlchemy row objects to dictionaries with JSON-safe values.

### `_norm_str_list(val)`
Normalizes various input formats to a list of strings:
- List → List (unchanged)
- JSON array string `'["A","B"]'` → List
- CSV string `"A, B, C"` → List
- Single value → Single-item list
- None → None

## Integration

The `mcp_bills` server is integrated into the main application via `main.py`:

```python
from mcp_servers.mcp_bills import mcp_bills
await main_mcp.import_server(mcp_bills, prefix="bills")
```

This makes all bills tools available under the "bills" prefix.

## Security Features

1. **SQL Injection Prevention**: Uses parameterized queries with SQLAlchemy
2. **Input Validation**: Comprehensive Pydantic validation
3. **Database Validation**: Validates foreign keys exist before insertion
4. **Soft Deletes**: Respects soft delete flags (is_deleted)
5. **Limited Results**: Returns maximum 5 rows to prevent excessive data transfer

## Usage Examples

### Searching Bills
```python
# Search by project IDs
result = search_bills(
    project_ids=["PROJ001", "PROJ002"],
    order_by="created_at",
    order_dir="desc"
)

# Search by customer and date range
result = search_bills(
    customer_ids="CUST001",
    created_at_from="2026-01-01",
    created_at_to="2026-01-31"
)
```

### Creating a Bill
```python
from mcp_servers.mcp_bills import BillCreateInfo, BillDetailsInfo

bill_info = BillCreateInfo(
    customer_id="CUST001",
    payer_code="PAY001",
    project_id="PROJ001",
    expected_date_of_payment="2026-01-30",
    execution_team="Team A",
    details=[
        BillDetailsInfo(
            attribute="Installation work",
            product="Product A",
            quantity=5,
            tax_amount=1000.0,
            amount=10000
        )
    ]
)

result = bills_create(information_create_invoice=bill_info)
```

## Testing

A comprehensive test suite is provided in `test_mcp_bills.py` that validates:
- BillDetailsInfo validation (quantity, amount)
- Helper function behavior (_norm_str_list)
- Data type conversions
- Edge cases and error conditions

Run tests with:
```bash
python test_mcp_bills.py
```

## Future Enhancements (Commented Functions)

The following functions are commented out for future implementation:
- `bills_update`: Update existing bills
- `bills_list`: List all bills with pagination
- `bills_list_by_creation_date`: List bills filtered by creation date

These follow the same pattern as other MCP servers in the project and can be implemented as needed.

## Notes

- The module uses PostgreSQL-specific features (sequence, ILIKE)
- All monetary values use Decimal for precision
- Timestamps are stored without timezone information
- The bill ID is automatically generated using a PostgreSQL sequence
