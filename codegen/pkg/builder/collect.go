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
	// Track which tags reference each schema
	schemaRefs := make(map[string][]string)

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
					if !slices.Contains(schemaRefs[schema.GetReference()], tagLower) {
						schemaRefs[schema.GetReference()] = append(schemaRefs[schema.GetReference()], tagLower)
					}
				}
			}
		}
	}

	// Identify schemas that are referenced by multiple tags and move them to shared
	for schemaRef, tags := range schemaRefs {
		if len(tags) > 1 {
			// Remove from individual tags
			for _, tag := range tags {
				tagLower := strings.ToLower(tag)
				idx := slices.IndexFunc(schemasByTag[tagLower], func(sp *base.SchemaProxy) bool {
					return sp.GetReference() == schemaRef
				})
				if idx != -1 {
					schemasByTag[tagLower] = append(schemasByTag[tagLower][:idx], schemasByTag[tagLower][idx+1:]...)
				}
			}
			// Add to shared
			if schemasByTag["_shared"] == nil {
				schemasByTag["_shared"] = make([]*base.SchemaProxy, 0)
			}
			// Find the schema proxy to add
			for _, schemas := range schemasByTag {
				for _, sp := range schemas {
					if sp.GetReference() == schemaRef {
						if !slices.ContainsFunc(schemasByTag["_shared"], func(existing *base.SchemaProxy) bool {
							return existing.GetReference() == schemaRef
						}) {
							schemasByTag["_shared"] = append(schemasByTag["_shared"], sp)
						}
						break
					}
				}
			}
		}
	}

	// Need to find schemas that were removed from other tags but not added yet
	for schemaRef, tags := range schemaRefs {
		if len(tags) > 1 {
			// Try to find this schema in any tag's collection from the original data
			var foundSchema *base.SchemaProxy
			for _, pathItem := range b.spec.Paths.PathItems.FromOldest() {
				for _, op := range pathItem.GetOperations().FromOldest() {
					c := make(SchemaProxyCollection, 0, 100)
					c.collectSchemasInResponse(op)
					c.collectSchemasInParams(op)
					c.collectSchemasInRequest(op)
					
					for _, schema := range c {
						if schema.GetReference() == schemaRef {
							foundSchema = schema
							break
						}
					}
					if foundSchema != nil {
						break
					}
				}
				if foundSchema != nil {
					break
				}
			}
			
			if foundSchema != nil && !slices.ContainsFunc(schemasByTag["_shared"], func(sp *base.SchemaProxy) bool {
				return sp.GetReference() == schemaRef
			}) {
				if schemasByTag["_shared"] == nil {
					schemasByTag["_shared"] = make([]*base.SchemaProxy, 0)
				}
				schemasByTag["_shared"] = append(schemasByTag["_shared"], foundSchema)
			}
		}
	}

	b.schemasByTag = schemasByTag
}

type SchemaProxyCollection []*base.SchemaProxy

// Collect the schemas that are referenced in the response body of the given operation.
func (c *SchemaProxyCollection) collectSchemasInResponse(op *v3.Operation) {
	if op.Responses == nil || op.Responses.Codes.Len() == 0 {
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
	if schema == nil {
		return
	}

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
