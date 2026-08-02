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
    go -C codegen run . generate \
        --out ../sumup/ \
        ../openapi.json

# Generate the versioned Python code sample catalog
[group('misc')]
generate-codesamples output="code-samples.json":
    go -C codegen run . samples \
        --sdk-version-file ../sumup/_version.py \
        --out "{{ absolute_path(output) }}" \
        ../openapi.json

[group('test')]
test:
    uv pip install -e .
    uv run pytest
