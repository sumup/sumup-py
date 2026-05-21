package builder

import (
	"strings"
	"testing"

	v3 "github.com/pb33f/libopenapi/datamodel/high/v3"
)

func TestMethodDocIncludesRaisesForDocumentedErrors(t *testing.T) {
	t.Parallel()

	doc := methodDoc(&v3.Operation{
		Summary:     "Create a checkout",
		Description: "Creates a new checkout.",
	}, []Response{
		{Code: 201},
		{Code: 400, IsErr: true, ErrDescription: "The request body is invalid."},
		{Code: 401, IsErr: true, ErrDescription: "The request is not authorized."},
	})

	if !strings.Contains(doc, "Raises:\n    APIError:") {
		t.Fatalf("expected Raises section in docstring, got %q", doc)
	}

	if !strings.Contains(doc, "400: The request body is invalid.") {
		t.Fatalf("expected 400 response in Raises section, got %q", doc)
	}

	if !strings.Contains(doc, "401: The request is not authorized.") {
		t.Fatalf("expected 401 response in Raises section, got %q", doc)
	}

	if !strings.Contains(doc, "Unexpected response statuses also raise this exception.") {
		t.Fatalf("expected unexpected response note in Raises section, got %q", doc)
	}
}

func TestMethodDocIncludesRaisesForUnexpectedResponsesOnly(t *testing.T) {
	t.Parallel()

	doc := methodDoc(&v3.Operation{
		Summary:     "Ping",
		Description: "Checks service health.",
	}, []Response{
		{Code: 204},
	})

	if !strings.Contains(doc, "Raises:\n    APIError: Raised when the API returns an unexpected response.") {
		t.Fatalf("expected fallback Raises section in docstring, got %q", doc)
	}
}
