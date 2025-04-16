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

# Check and auto-fix py files
[group('lint')]
check-fix:
    uv run ruff check --fix

# Generate code from OpenAPI specs
[group('misc')]
generate: && fmt check-fix
    py-sdk-gen generate --out sumup --module sumup --package sumup --name 'SumUp' ./openapi.json
