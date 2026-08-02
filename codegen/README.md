<div align="center">

# sumup-py codegen

A highly opinionated OpenAPI specs to SDK generator for [sumup-py](https://github.com/sumup/sumup-py).

</div>

## Python SDK

The `generate` command reads `openapi.json` and generates the Python client, resources, request types, and response types. Generate the SDK from the repository root with:

```sh
just generate
```

## Python Code Samples

The `samples` command generates a deterministic, versioned JSON catalog from the same intermediate representation used to generate the SDK. Each entry contains a complete Python program, and named OpenAPI request examples produce separate entries.

Generate the catalog from the repository root with:

```sh
just generate-codesamples
```

The recipe writes `code-samples.json` in the repository root by default. Pass another path as its argument to use a different destination. The codegen test suite compiles every generated program, and the release workflow sends the release-tag catalog to `src/codesamples/python.json` in `sumup/sumup-developer`; generated JSON is not committed to this repository.
