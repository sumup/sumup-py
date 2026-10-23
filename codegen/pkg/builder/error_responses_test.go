package builder

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/pb33f/libopenapi"
)

func TestGenerateErrorResponseTypes(t *testing.T) {
	t.Parallel()

	document, err := libopenapi.NewDocument([]byte(`{
  "openapi": "3.1.0",
  "info": {"title": "Errors", "version": "1.0.0"},
  "paths": {
    "/things": {
      "get": {
        "tags": ["Things"],
        "operationId": "GetThing",
        "responses": {
          "200": {"description": "Success", "content": {"application/json": {
            "schema": {"$ref": "#/components/schemas/Thing"}
          }}},
          "400": {"description": "Invalid", "content": {"application/json": {
            "schema": {"oneOf": [
              {"$ref": "#/components/schemas/Error"},
              {"type": "array", "items": {"$ref": "#/components/schemas/Error"}}
            ]}
          }, "application/problem+json": {
            "schema": {"$ref": "#/components/schemas/Problem"}
          }}},
          "401": {"$ref": "#/components/responses/Unauthorized"},
          "422": {"description": "Validation errors", "content": {"application/json": {
            "schema": {"type": "array", "items": {"$ref": "#/components/schemas/Problem"}}
          }}},
          "500": {"description": "Unknown error", "content": {"application/json": {}}}
        }
      }
    }
  },
  "components": {
    "responses": {
      "Unauthorized": {"description": "Unauthorized", "content": {"application/problem+json": {
        "schema": {"$ref": "#/components/schemas/Problem"}
      }}}
    },
    "schemas": {
      "Thing": {"type": "object", "properties": {"id": {"type": "string"}}},
      "Error": {"type": "object", "properties": {"message": {"type": "string"}}},
      "Problem": {"type": "object", "required": ["type"], "properties": {"type": {"type": "string"}}}
    }
  }
}`))
	if err != nil {
		t.Fatal(err)
	}
	model, err := document.BuildV3Model()
	if err != nil {
		t.Fatal(err)
	}
	out := t.TempDir()
	cwd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	relativeOut, err := filepath.Rel(cwd, out)
	if err != nil {
		t.Fatal(err)
	}
	generator := New(Config{Out: relativeOut})
	if err := generator.Load(&model.Model); err != nil {
		t.Fatal(err)
	}
	if err := generator.Build(); err != nil {
		t.Fatal(err)
	}

	checks := map[string][]string{
		"types/__init__.py": {
			"GetThingJson400Response = Error | list[Error]",
			"GetThing422Response = list[Problem]",
		},
		"things/resource.py": {
			`content_type == "application/json"`,
			`content_type == "application/problem+json"`,
			`APIError.from_response("Invalid", resp, body_type=GetThingJson400Response)`,
			`APIError.from_response("Invalid", resp, body_type=Problem)`,
			"raises BadRequestError",
			`APIError.from_response("Validation errors", resp, body_type=GetThing422Response)`,
			`APIError.from_response("Unauthorized", resp, body_type=Problem)`,
			`APIError.from_response("Unknown error", resp)`,
			"-> Thing:",
			"with _wrap_request_errors():",
		},
		"things/__init__.py": {`"GetThingJson400Response"`, `"GetThing422Response"`},
	}
	for filename, snippets := range checks {
		data, err := os.ReadFile(filepath.Join(out, filename))
		if err != nil {
			t.Fatal(err)
		}
		for _, snippet := range snippets {
			if !strings.Contains(string(data), snippet) {
				t.Errorf("%s missing %q", filename, snippet)
			}
		}
	}
}
