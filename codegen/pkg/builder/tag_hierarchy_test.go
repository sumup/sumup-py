package builder

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/pb33f/libopenapi"
)

func TestNestedReaderResources(t *testing.T) {
	t.Parallel()

	doc, err := libopenapi.NewDocument([]byte(`
openapi: 3.1.0
info: {title: Readers, version: 1.0.0}
tags:
  - name: Readers
  - name: ReaderCheckouts
    x-displayName: Checkouts
x-tagGroups:
  - name: Readers
    tags: [ReaderCheckouts]
paths:
  /readers/checkouts:
    get:
      operationId: ListReaders
      tags: [Readers]
      responses:
        '204': {description: OK}
    post:
      operationId: CreateReaderCheckout
      tags: [ReaderCheckouts]
      x-codegen: {method_name: create}
      responses:
        '204': {description: OK}
components: {schemas: {}}
`))
	if err != nil {
		t.Fatal(err)
	}
	model, err := doc.BuildV3Model()
	if err != nil {
		t.Fatal(err)
	}

	out := t.TempDir()
	builder := New(Config{Out: out})
	if err := builder.Load(&model.Model); err != nil {
		t.Fatal(err)
	}
	child := builder.pathsByTag["readercheckouts"].PathItems.GetOrZero("/readers/checkouts")
	if child.Get != nil || child.Post == nil {
		t.Fatal("the child must only contain its own operation")
	}
	parent := builder.pathsByTag["readers"].PathItems.GetOrZero("/readers/checkouts")
	if parent.Get == nil || parent.Post != nil {
		t.Fatal("the parent must only contain its own operation")
	}
	method, err := builder.operationToMethod("POST", "/readers/checkouts", child.Post)
	if err != nil {
		t.Fatal(err)
	}
	if method.FunctionName != "create" {
		t.Errorf("unexpected checkout method name: %s", method.FunctionName)
	}
	if path := builder.resourcePath("readercheckouts"); path != "readers.checkouts" {
		t.Fatalf("wrong resource path %q", path)
	}
	if err := builder.Build(); err != nil {
		t.Fatal(err)
	}
	for file, want := range map[string]string{
		"readers/resource.py":           "from .checkouts import ReaderCheckoutsResource, AsyncReaderCheckoutsResource",
		"readers/checkouts/__init__.py": "from .resource import (",
		"readers/checkouts/resource.py": "from ..._service import Resource",
	} {
		content, err := os.ReadFile(filepath.Join(out, filepath.FromSlash(file)))
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(string(content), want) {
			t.Errorf("%s is missing %q", file, want)
		}
	}
}

func TestResourceParentCycleAfterNormalization(t *testing.T) {
	t.Parallel()
	doc, err := libopenapi.NewDocument([]byte(`
openapi: 3.1.0
info: {title: Test, version: 1.0.0}
paths: {}
tags: [{name: A}, {name: B}, {name: a}]
x-tagGroups: [{name: A, tags: [B]}, {name: B, tags: [a]}]
`))
	if err != nil {
		t.Fatal(err)
	}
	model, err := doc.BuildV3Model()
	if err != nil {
		t.Fatal(err)
	}
	if _, err := readResourceParents(&model.Model); err == nil {
		t.Fatal("expected a cycle error for the normalized resource tags")
	}
}
