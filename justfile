set quiet

_default: _help

_help:
    just --list

build:
    uv build

# Format py files
[group('lint')]
fmt:
    uv run ruff format

# Check py files
[group('lint')]
check:
    uv run ruff check
    uv run ty check

# Check and auto-fix py files
[group('lint')]
check-fix:
    uv run ruff check --fix

# Generate code from OpenAPI specs
[group('misc')]
generate: && fmt check-fix
    cd codegen && go run ./... generate --out ../sumup/ ../openapi.json
