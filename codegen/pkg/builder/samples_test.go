package builder

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
	"strings"
	"testing"

	"github.com/pb33f/libopenapi"
)

func TestBuilderSamples(t *testing.T) {
	t.Parallel()

	_, catalog, expectedSamples := testSampleCatalog(t)
	if catalog.SchemaVersion != 1 {
		t.Fatalf("SchemaVersion = %d, want 1", catalog.SchemaVersion)
	}
	if catalog.SDK.Module != "sumup" {
		t.Fatalf("SDK.Module = %q, want sumup", catalog.SDK.Module)
	}
	if catalog.Language != "python" {
		t.Fatalf("Language = %q, want python", catalog.Language)
	}
	if catalog.OpenAPIVersion != "1.0.0" {
		t.Fatalf("OpenAPIVersion = %q, want 1.0.0", catalog.OpenAPIVersion)
	}
	if len(catalog.Samples) != expectedSamples {
		t.Fatalf("len(Samples) = %d, want %d", len(catalog.Samples), expectedSamples)
	}
	if !slices.IsSortedFunc(catalog.Samples, func(a, b Sample) int {
		return strings.Compare(a.ID, b.ID)
	}) {
		t.Fatal("samples are not sorted by ID")
	}

	seen := make(map[string]struct{}, len(catalog.Samples))
	for _, sample := range catalog.Samples {
		if _, ok := seen[sample.ID]; ok {
			t.Fatalf("duplicate sample ID %q", sample.ID)
		}
		seen[sample.ID] = struct{}{}
	}

	hostedCheckout := sampleByID(t, catalog.Samples, "CreateCheckout.HostedCheckout")
	if !strings.Contains(hostedCheckout.Source, "client.checkouts.create(") {
		t.Fatalf("CreateCheckout sample does not call the generated SDK method:\n%s", hostedCheckout.Source)
	}
	if !strings.Contains(hostedCheckout.Source, "hosted_checkout={") ||
		!strings.Contains(hostedCheckout.Source, `"enabled": True`) {
		t.Fatalf("CreateCheckout sample does not use the OpenAPI example:\n%s", hostedCheckout.Source)
	}
	encodedSample, err := json.Marshal(hostedCheckout)
	if err != nil {
		t.Fatalf("marshal CreateCheckout sample: %v", err)
	}
	if !strings.Contains(string(encodedSample), `"sample":`) {
		t.Fatalf("sample JSON does not preserve the portal contract: %s", encodedSample)
	}
	if strings.Contains(string(encodedSample), `"source":`) {
		t.Fatalf("sample JSON contains internal source field name: %s", encodedSample)
	}

	compilePythonSamples(t, catalog.Samples)
}

func TestBuilderSamplesDeterministic(t *testing.T) {
	t.Parallel()

	_, first, _ := testSampleCatalog(t)
	_, second, _ := testSampleCatalog(t)
	firstJSON, err := json.Marshal(first)
	if err != nil {
		t.Fatalf("marshal first catalog: %v", err)
	}
	secondJSON, err := json.Marshal(second)
	if err != nil {
		t.Fatalf("marshal second catalog: %v", err)
	}
	if string(firstJSON) != string(secondJSON) {
		t.Fatal("sample generation is not deterministic")
	}
}

func testSampleCatalog(t *testing.T) (string, *SampleCatalog, int) {
	t.Helper()

	repositoryRoot, err := filepath.Abs(filepath.Join("..", "..", ".."))
	if err != nil {
		t.Fatalf("resolve repository root: %v", err)
	}
	spec, err := os.ReadFile(filepath.Join(repositoryRoot, "openapi.json"))
	if err != nil {
		t.Fatalf("read OpenAPI document: %v", err)
	}
	document, err := libopenapi.NewDocument(spec)
	if err != nil {
		t.Fatalf("load OpenAPI document: %v", err)
	}
	model, err := document.BuildV3Model()
	if err != nil {
		t.Fatalf("build OpenAPI model: %v", err)
	}

	generator := New(Config{})
	if err := generator.Load(&model.Model); err != nil {
		t.Fatalf("load builder: %v", err)
	}
	catalog, err := generator.Samples("test")
	if err != nil {
		t.Fatalf("generate samples: %v", err)
	}
	expectedSamples := 0
	for _, pathItem := range model.Model.Paths.PathItems.FromOldest() {
		for _, operation := range pathItem.GetOperations().FromOldest() {
			expectedSamples += len(requestExamples(operation))
		}
	}
	return repositoryRoot, catalog, expectedSamples
}

func sampleByID(t *testing.T, samples []Sample, id string) Sample {
	t.Helper()
	for _, sample := range samples {
		if sample.ID == id {
			return sample
		}
	}
	t.Fatalf("sample %q not found", id)
	return Sample{}
}

func compilePythonSamples(t *testing.T, samples []Sample) {
	t.Helper()

	python, err := exec.LookPath("python3")
	if err != nil {
		t.Fatalf("find python3 for generated sample validation: %v", err)
	}
	dir := t.TempDir()
	args := []string{"-m", "py_compile"}
	for i, sample := range samples {
		filename := filepath.Join(dir, fmt.Sprintf("sample%03d.py", i))
		if err := os.WriteFile(filename, []byte(sample.Source), 0o600); err != nil {
			t.Fatalf("write sample %q: %v", sample.ID, err)
		}
		args = append(args, filename)
	}

	command := exec.CommandContext(t.Context(), python, args...)
	if output, err := command.CombinedOutput(); err != nil {
		t.Fatalf("compile generated Python samples: %v\n%s", err, output)
	}
}
