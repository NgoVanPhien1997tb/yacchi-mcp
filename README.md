# Yacchi MCP - Bills Management System

## Tổng Quan (Overview)

Hệ thống quản lý hóa đơn/thanh toán sử dụng FastMCP framework.

This is a bills/payment management system built with FastMCP framework.

## Trạng Thái (Status)

✅ **MCP Bills Module: HOÀN THÀNH (COMPLETE)**

Module `mcp_bills` đã được triển khai đầy đủ với các tính năng:
- ✅ Tìm kiếm hóa đơn (Search bills)
- ✅ Tạo hóa đơn (Create bills)
- ✅ Xác thực dữ liệu (Data validation)
- ✅ Tài liệu đầy đủ (Complete documentation)
- ✅ Kiểm thử toàn diện (Comprehensive tests)

## Tài Liệu (Documentation)

1. **[HUONG_DAN_SU_DUNG_MCP_BILLS.md](HUONG_DAN_SU_DUNG_MCP_BILLS.md)** - Hướng dẫn sử dụng (Vietnamese)
2. **[MCP_BILLS_DOCUMENTATION.md](MCP_BILLS_DOCUMENTATION.md)** - Technical documentation (English)

## Cài Đặt (Installation)

```bash
# Clone repository
git clone https://github.com/NgoVanPhien1997tb/yacchi-mcp.git
cd yacchi-mcp

# Install dependencies
pip install fastmcp psycopg2-binary python-dotenv sqlalchemy

# Configure database
cp .env.example .env
# Edit .env and set DATABASE_URL
```

## Sử Dụng (Usage)

```bash
# Run server
python main.py

# Run tests
python test_mcp_bills.py
```

## Cấu Trúc Dự Án (Project Structure)

```
yacchi-mcp/
├── db/                          # Database models and connection
│   ├── models/
│   │   ├── bills.py            # PaymentPlan model
│   │   ├── bills_details.py    # PaymentPlanDetail model
│   │   ├── customers.py
│   │   └── projects.py
│   └── connection.py
├── mcp_servers/                 # MCP server modules
│   ├── mcp_bills.py            # ✅ Bills management (COMPLETE)
│   ├── mcp_customer.py         # Customer management
│   ├── mcp_payment.py          # Payment management
│   └── mcp_projects.py         # Project management
├── main.py                      # Main application entry point
├── test_mcp_bills.py           # Validation tests
├── HUONG_DAN_SU_DUNG_MCP_BILLS.md  # User guide (Vietnamese)
└── MCP_BILLS_DOCUMENTATION.md      # Technical docs (English)
```

## Tính Năng (Features)

### MCP Bills (Hoàn Thành / Complete)
- ✅ **search_bills**: Tìm kiếm hóa đơn theo dự án, khách hàng, ngày tạo
- ✅ **create_bill**: Tạo hóa đơn mới với xác thực đầy đủ
- ✅ **bills_create_prompt**: Gợi ý tạo hóa đơn

### MCP Customers
- ✅ **search_customers**: Tìm kiếm khách hàng
- ✅ **update_customer**: Cập nhật thông tin khách hàng

### MCP Projects
- ✅ **project_search**: Tìm kiếm dự án
- ✅ **cost_quotation_for_project**: Lấy báo giá dự án
- ✅ **project_list_by_customer_ids**: Liệt kê dự án theo khách hàng

## Kiểm Thử (Testing)

```bash
# Run validation tests
python test_mcp_bills.py

# Expected output:
# ============================================================
# MCP Bills Validation Tests
# ============================================================
# ...
# ✅ All tests passed!
# ============================================================
```

## Yêu Cầu Hệ Thống (Requirements)

- Python >= 3.12
- PostgreSQL database
- Dependencies (see `pyproject.toml`)

## Bảo Mật (Security)

✅ Không có lỗ hổng bảo mật phát hiện (No security vulnerabilities detected)

- SQL injection prevention
- Input validation with Pydantic
- Database foreign key validation
- Soft delete support
- Result limiting

## Đóng Góp (Contributing)

Vui lòng tham khảo tài liệu trong thư mục để hiểu cách thức hoạt động trước khi đóng góp.

Please review the documentation to understand how things work before contributing.

## Giấy Phép (License)

[Add your license information here]

## Liên Hệ (Contact)

- GitHub: [@NgoVanPhien1997tb](https://github.com/NgoVanPhien1997tb)

---

**Trạng thái Triển Khai: ✅ Hoàn Thành**  
**Deployment Status: ✅ Complete**
