# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

# ---- System deps
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    UV_LINK_MODE=copy \
    PORT=9000

WORKDIR /app

# (Tuỳ chọn) tối ưu hoá mirror/apt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# ---- Install uv (Astral)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# ---- Only copy files cần cho dependency resolution trước để cache
COPY pyproject.toml uv.lock ./

# Cài deps production (không cài dev)
RUN uv sync --frozen --no-dev

# ---- Copy source
# Giữ đúng cây thư mục của bạn
COPY . .

# (Khuyến nghị) tạo user non-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (server http của MCP)
EXPOSE ${PORT}

# Nếu dùng .env, hãy nạp qua docker run/compose (env_file)
# Lệnh chạy: chỉnh sửa theo cách bạn khởi động server trong main.py
CMD ["uv", "run", "python", "main.py"]

