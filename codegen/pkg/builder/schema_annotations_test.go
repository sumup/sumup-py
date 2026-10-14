package builder

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/pb33f/libopenapi"
)

func TestGenerateAnnotatedSchemas(t *testing.T) {
	t.Parallel()
	spec, err := os.ReadFile("testdata/schema-annotations.json")
	if err != nil {
		t.Fatal(err)
	}
	document, err := libopenapi.NewDocument(spec)
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
	data, err := os.ReadFile(filepath.Join(out, "types", "__init__.py"))
	if err != nil {
		t.Fatal(err)
	}
	_, body, ok := strings.Cut(string(data), "class ExtendedAddress(")
	if !ok {
		t.Fatal("missing ExtendedAddress")
	}
	body, _, _ = strings.Cut(body, "\nclass ")
	for _, field := range []string{"country: CountryCode", "city: str", "label: str"} {
		if !strings.Contains(body, field) {
			t.Errorf("ExtendedAddress missing %s", field)
		}
	}
	checks := map[string][]string{
		"types/__init__.py":     {"country: CountryCode", "phone_number: PhoneNumber", "class ExtendedAddress", "label: str"},
		"merchants/__init__.py": {"\"Address\"", "\"CountryCode\"", "\"PhoneNumber\""},
	}
	for file, snippets := range checks {
		data, err := os.ReadFile(filepath.Join(out, file))
		if err != nil {
			t.Fatal(err)
		}
		for _, snippet := range snippets {
			if !strings.Contains(string(data), snippet) {
				t.Errorf("%s missing %q:\n%s", file, snippet, data)
			}
		}
	}
}

func TestAnnotationNormalizationPreservesConstraints(t *testing.T) {
	t.Parallel()
	document, err := libopenapi.NewDocument([]byte(`{"openapi":"3.1.0","info":{"title":"test","version":"1"},"paths":{},"components":{"schemas":{"Code":{"type":"string"},"Constrained":{"allOf":[{"$ref":"#/components/schemas/Code"},{"minLength":2}]}}}}`))
	if err != nil {
		t.Fatal(err)
	}
	model, err := document.BuildV3Model()
	if err != nil {
		t.Fatal(err)
	}
	normalizeSchemaAnnotations(&model.Model)
	constrained := model.Model.Components.Schemas.GetOrZero("Constrained").Schema()
	if len(constrained.AllOf) != 2 {
		t.Fatal("normalization removed a validation constraint")
	}
}

func TestAnnotatedRecursiveReferences(t *testing.T) {
	t.Parallel()
	document, err := libopenapi.NewDocument([]byte(`{"openapi":"3.1.0","info":{"title":"test","version":"1"},"paths":{"/nodes":{"get":{"tags":["Nodes"],"operationId":"GetNode","responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Node"}}}}}}}},"components":{"schemas":{"Node":{"type":"object","properties":{"next":{"$ref":"#/components/schemas/Node","description":"Next node."}}}}}}`))
	if err != nil {
		t.Fatal(err)
	}
	model, err := document.BuildV3Model()
	if err != nil {
		t.Fatal(err)
	}
	generator := New(Config{})
	if err := generator.Load(&model.Model); err != nil {
		t.Fatal(err)
	}
}

func TestAnnotationNormalizationPreservesNamedReferences(t *testing.T) {
	t.Parallel()
	document, err := libopenapi.NewDocument([]byte(`{"openapi":"3.1.0","info":{"title":"test","version":"1"},"paths":{},"components":{"schemas":{"Code":{"type":"string"},"Alias":{"allOf":[{"description":"Alias documentation."},{"$ref":"#/components/schemas/Code"}]},"Holder":{"type":"object","properties":{"code":{"$ref":"#/components/schemas/Alias"}}}}}}`))
	if err != nil {
		t.Fatal(err)
	}
	model, err := document.BuildV3Model()
	if err != nil {
		t.Fatal(err)
	}
	normalizeSchemaAnnotations(&model.Model)
	property := model.Model.Components.Schemas.GetOrZero("Holder").Schema().Properties.GetOrZero("code")
	if got := property.GetReference(); got != "#/components/schemas/Alias" {
		t.Fatalf("reference = %q, want Alias", got)
	}
	if got := property.Schema().Description; got != "Alias documentation." {
		t.Fatalf("description = %q", got)
	}
}

func TestAnnotationNormalizationPreservesObjectDependencies(t *testing.T) {
	t.Parallel()
	document, err := libopenapi.NewDocument([]byte(`{"openapi":"3.1.0","info":{"title":"test","version":"1"},"paths":{},"components":{"schemas":{"Base":{"type":"object","properties":{"id":{"type":"string"}}},"Derived":{"allOf":[{"$ref":"#/components/schemas/Base","description":"Inherited fields."}]}}}}`))
	if err != nil {
		t.Fatal(err)
	}
	model, err := document.BuildV3Model()
	if err != nil {
		t.Fatal(err)
	}
	normalizeSchemaAnnotations(&model.Model)
	derived := model.Model.Components.Schemas.GetOrZero("Derived").Schema()
	if len(derived.AllOf) != 1 || derived.AllOf[0].GetReference() != "#/components/schemas/Base" {
		t.Fatal("object dependency was removed")
	}
}
