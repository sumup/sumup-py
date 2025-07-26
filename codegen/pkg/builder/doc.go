package builder

import (
	"fmt"
	"slices"
	"strings"

	"github.com/pb33f/libopenapi/datamodel/high/base"
	v3 "github.com/pb33f/libopenapi/datamodel/high/v3"
	"gopkg.in/yaml.v3"

	"github.com/sumup/sumup-py/codegen/pkg/extension"
)

func deprecationNotice(operation *v3.Operation) *string {
	if operation.Deprecated != nil && *operation.Deprecated {
		if notice, ok := extension.Get[string](operation.Extensions, "x-deprecation-notice"); ok {
			return &notice
		} else {
			defaultDeprecationNotice := "This method is deprecated"
			return &defaultDeprecationNotice
		}
	}

	return nil
}

// methodDoc creates godoc comment for an operation.
func methodDoc(operation *v3.Operation) string {
	out := new(strings.Builder)

	if operation.Summary != "" {
		fmt.Fprintf(out, "%s\n\n", operation.Summary)
	}

	fmt.Fprintf(out, "%s\n", operation.Description)

	if operation.ExternalDocs != nil {
		extDescription := operation.ExternalDocs.Description
		if extDescription == "" {
			extDescription = "See"
		}

		fmt.Fprintf(out, "\n%s: %s\n", extDescription, operation.ExternalDocs.URL)
	}

	return formatDoc(out.String())
}

// operationParamsDoc creates godoc comment for a struct representing
// parameters of an operation.
func operationParamsDoc(name string, operation *v3.Operation) string {
	return formatDoc(name + ": query parameters for " + operation.OperationId)
}

// schemaDoc creates godoc for a schema.
func schemaDoc(name string, schema *base.Schema) string {
	out := new(strings.Builder)

	if schema.Description != "" {
		fmt.Fprint(out, schema.Description)
	} else {
		fmt.Fprintf(out, "%s is a schema definition.", name)
	}

	writeSchemaMetainfo(out, schema)

	return formatDoc(out.String())
}

// schemaPropertyGodoc creates godoc for a schema property.
func schemaPropertyGodoc(s *base.Schema) string {
	out := new(strings.Builder)

	fmt.Fprint(out, strings.TrimSpace(s.Description))

	writeSchemaMetainfo(out, s)

	return formatDoc(out.String())
}

// parameterPropertyDoc creates godoc for a request parameter property.
func parameterPropertyDoc(s *base.Schema) string {
	out := new(strings.Builder)

	fmt.Fprint(out, strings.TrimSpace(s.Description))

	return formatDoc(out.String())
}

// writeSchemaMetainfo writes additional schema metainfo such as validations
// into the output.
func writeSchemaMetainfo(out *strings.Builder, schema *base.Schema) {
	if schema.ReadOnly != nil && *schema.ReadOnly {
		fmt.Fprintf(out, "\nRead only")
	}

	if schema.WriteOnly != nil && *schema.WriteOnly {
		fmt.Fprintf(out, "\nWrite only")
	}

	// add format but only if it can't be inferred from the type itself
	if !slices.Contains([]string{"", "date-time", "float"}, schema.Format) {
		fmt.Fprintf(out, "\nFormat: %v", schema.Format)
	}

	if schema.Default != nil {
		if def, err := yaml.Marshal(schema.Default); err == nil {
			fmt.Fprintf(out, "\nDefault: %s", def)
		}
	}

	// strings
	if schema.MinLength != nil {
		fmt.Fprintf(out, "\nMin length: %v", *schema.MinLength)
	}
	if schema.MaxLength != nil {
		fmt.Fprintf(out, "\nMax length: %v", *schema.MaxLength)
	}
	if schema.Pattern != "" {
		fmt.Fprintf(out, "\nPattern: %v", schema.Pattern)
	}

	// numbers
	if schema.Minimum != nil {
		fmt.Fprintf(out, "\nMin: %v", *schema.Minimum)
	}
	if schema.Maximum != nil {
		fmt.Fprintf(out, "\nMax: %v", *schema.Maximum)
	}
	if schema.MultipleOf != nil {
		fmt.Fprintf(out, "\nMultiple of: %v", *schema.MultipleOf)
	}

	// arrays
	if schema.UniqueItems != nil && *schema.UniqueItems {
		fmt.Fprintf(out, "\nUnique items only")
	}
	if schema.MinItems != nil {
		fmt.Fprintf(out, "\nMin items: %v", *schema.MinItems)
	}
	if schema.MaxItems != nil {
		fmt.Fprintf(out, "\nMax items: %v", *schema.MaxItems)
	}

	// objects
	if schema.MinProperties != nil {
		fmt.Fprintf(out, "\nMin properties: %v", *schema.MinProperties)
	}
	if schema.MaxProperties != nil {
		fmt.Fprintf(out, "\nMax properties: %v", *schema.MaxProperties)
	}

	if schema.ExternalDocs != nil {
		extDescription := schema.ExternalDocs.Description
		if extDescription == "" {
			extDescription = "See"
		}

		fmt.Fprintf(out, "\n%s: %s", extDescription, schema.ExternalDocs.URL)
	}

	if schema.Deprecated != nil && *schema.Deprecated {
		if notice, ok := extension.Get[string](schema.Extensions, "x-deprecation-notice"); ok {
			fmt.Fprintf(out, "\nDeprecated: %s", notice)
		} else {
			fmt.Fprint(out, "\nDeprecated: this operation is deprecated")
		}
	}
}

// splitDocString inserts newlines into doc comments at approximately 100 character intervals.
func formatDoc(s string) string {
	out := new(strings.Builder)

	var written int
	for _, subStr := range strings.SplitAfter(s, " ") {
		if written > 100 {
			// Remove trailing space if inserting a newline.
			out.WriteString(strings.TrimSuffix(subStr, " "))
			written = 0

			continue
		}

		ct, _ := out.WriteString(subStr)
		written += ct

		if strings.Contains(subStr, "\n") {
			written = 0
		}
	}

	return strings.TrimSpace(out.String())
}
