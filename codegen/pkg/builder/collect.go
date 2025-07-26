package builder

import (
	"log/slog"
	"slices"
	"strings"

	"github.com/pb33f/libopenapi/datamodel/high/base"
	v3 "github.com/pb33f/libopenapi/datamodel/high/v3"
	v3low "github.com/pb33f/libopenapi/datamodel/low/v3"
)

func (b *Builder) collectPaths() {
	for path, pathSpec := range b.spec.Paths.PathItems.FromOldest() {
		for method, operationSpec := range pathSpec.GetOperations().FromOldest() {
			var tag string
			if len(operationSpec.Tags) > 1 {
				slog.Warn("multiple tags for operation, picking first tag",
					slog.String("path", path),
					slog.String("method", method),
				)

				tag = strings.ToLower(operationSpec.Tags[0])
			}

			if len(operationSpec.Tags) == 1 {
				tag = strings.ToLower(operationSpec.Tags[0])
			}

			if len(operationSpec.Tags) == 0 {
				slog.Error("no tags for operation",
					slog.String("path", path),
					slog.String("method", method),
				)
				continue
			}

			tagPaths, ok := b.pathsByTag[tag]
			if !ok {
				tagPaths = v3.NewPaths(&v3low.Paths{})
				b.pathsByTag[tag] = tagPaths
			}

			tagPaths.PathItems.Set(path, pathSpec)
		}
	}
}

func (b *Builder) collectSchemas() {
	// Map of schemas grouped by tag
	schemasByTag := make(map[string][]*base.SchemaProxy)

	for path, pathItem := range b.spec.Paths.PathItems.FromOldest() {
		for method, op := range pathItem.GetOperations().FromOldest() {
			c := make(SchemaProxyCollection, 0, 100)
			c.collectSchemasInResponse(op)
			c.collectSchemasInParams(op)
			c.collectSchemasInRequest(op)

			for _, schema := range c {
				if schema.GetReference() == "" {
					continue
				}

				if len(op.Tags) == 0 {
					slog.Error("no tags for schema under operation",
						slog.String("path", path),
						slog.String("method", method),
						slog.String("ref", schema.GetReference()),
					)
					continue
				}

				for _, tag := range op.Tags {
					tagLower := strings.ToLower(tag)
					if !slices.ContainsFunc(schemasByTag[tagLower], func(sp *base.SchemaProxy) bool {
						return sp.GetReference() == schema.GetReference()
					}) {
						schemasByTag[tagLower] = append(schemasByTag[tagLower], schema)
					}
				}
			}
		}
	}

	b.schemasByTag = schemasByTag
}

type SchemaProxyCollection []*base.SchemaProxy

// Collect the schemas that are referenced in the response body of the given operation.
func (c *SchemaProxyCollection) collectSchemasInResponse(op *v3.Operation) {
	if op.Responses == nil {
		return
	}

	for _, response := range op.Responses.Codes.FromOldest() {
		// TODO: handle content-type correctly
		for _, mediaType := range response.Content.FromOldest() {
			c.collectReferencedSchemas(mediaType.Schema)
		}
	}
}

// Collect the schemas that are referenced in the request parameters of the given operation.
func (c *SchemaProxyCollection) collectSchemasInParams(op *v3.Operation) {
	if op.RequestBody == nil {
		return
	}

	for _, param := range op.Parameters {
		c.collectReferencedSchemas(param.Schema)
	}
}

// Collect the schemas that are referenced in the request body of the given operation.
func (c *SchemaProxyCollection) collectSchemasInRequest(op *v3.Operation) {
	if op.RequestBody == nil {
		return
	}

	for _, mediaType := range op.RequestBody.Content.FromOldest() {
		c.collectReferencedSchemas(mediaType.Schema)
	}
}

// Collect the schemas that are referenced by the given schemas
func (c *SchemaProxyCollection) collectReferencedSchemas(schema *base.SchemaProxy) {
	if slices.Contains(schema.Schema().Type, "object") {
		for _, prop := range schema.Schema().Properties.FromOldest() {
			c.collectReferencedSchemas(prop)
		}
	}

	if slices.Contains(schema.Schema().Type, "array") && schema.Schema().Items != nil {
		c.collectReferencedSchemas(schema.Schema().Items.A)
	}

	for _, one := range schema.Schema().AnyOf {
		c.collectReferencedSchemas(one)
	}

	for _, one := range schema.Schema().AllOf {
		c.collectReferencedSchemas(one)
	}

	for _, one := range schema.Schema().OneOf {
		c.collectReferencedSchemas(one)
	}

	// append the schema itself last because we need schemas that it references
	// to come first in the generated code as the order of declarations matters
	if !slices.Contains(*c, schema) {
		*c = append(*c, schema)
	}
}
