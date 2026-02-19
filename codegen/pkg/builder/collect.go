package builder

import (
	"log/slog"
	"maps"
	"slices"
	"sort"
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
	if len(op.Parameters) == 0 {
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

	schemaDef := schema.Schema()

	if slices.Contains(schemaDef.Type, "object") {
		for _, prop := range schemaDef.Properties.FromOldest() {
			c.collectReferencedSchemas(prop)
		}
	}

	if slices.Contains(schemaDef.Type, "array") && schemaDef.Items != nil {
		c.collectReferencedSchemas(schemaDef.Items.A)
	}

	if schemaDef.AdditionalProperties != nil && schemaDef.AdditionalProperties.IsA() {
		c.collectReferencedSchemas(schemaDef.AdditionalProperties.A)
	}

	for _, one := range schemaDef.AnyOf {
		c.collectReferencedSchemas(one)
	}

	for _, one := range schemaDef.AllOf {
		c.collectReferencedSchemas(one)
	}

	for _, one := range schemaDef.OneOf {
		c.collectReferencedSchemas(one)
	}

	// append the schema itself last because we need schemas that it references
	// to come first in the generated code as the order of declarations matters
	if !slices.Contains(*c, schema) {
		*c = append(*c, schema)
	}
}

func (b *Builder) orderedComponentSchemaNames() []string {
	if b.spec == nil || b.spec.Components == nil || b.spec.Components.Schemas == nil {
		return nil
	}

	componentSchemas := make(map[string]*base.SchemaProxy)
	for name, schema := range b.spec.Components.Schemas.FromOldest() {
		componentSchemas[name] = schema
	}

	allNames := slices.Collect(maps.Keys(componentSchemas))
	sort.Strings(allNames)

	state := make(map[string]uint8)
	ordered := make([]string, 0, len(componentSchemas))
	var visit func(string)
	visit = func(name string) {
		switch state[name] {
		case 1:
			// Cycle detected. We cannot topologically sort cycles, but still continue
			// generation to avoid dropping schemas.
			return
		case 2:
			return
		}
		state[name] = 1

		refs := make(map[string]struct{})
		collectSchemaReferences(componentSchemas[name], refs)

		refNames := slices.Collect(maps.Keys(refs))
		sort.Strings(refNames)
		for _, dep := range refNames {
			if dep == name {
				continue
			}
			if _, ok := componentSchemas[dep]; ok {
				visit(dep)
			}
		}

		state[name] = 2
		ordered = append(ordered, name)
	}

	for _, name := range allNames {
		visit(name)
	}

	return ordered
}

func collectSchemaReferences(schema *base.SchemaProxy, refs map[string]struct{}) {
	if schema == nil {
		return
	}

	if schema.GetReference() != "" {
		if strings.HasPrefix(schema.GetReference(), "#/components/schemas/") {
			ref := strings.TrimPrefix(schema.GetReference(), "#/components/schemas/")
			refs[ref] = struct{}{}
		}
	}

	schemaDef := schema.Schema()
	if schemaDef == nil {
		return
	}

	for _, prop := range schemaDef.Properties.FromOldest() {
		collectSchemaReferences(prop, refs)
	}

	if schemaDef.Items != nil {
		collectSchemaReferences(schemaDef.Items.A, refs)
	}

	if schemaDef.AdditionalProperties != nil && schemaDef.AdditionalProperties.IsA() {
		collectSchemaReferences(schemaDef.AdditionalProperties.A, refs)
	}

	for _, one := range schemaDef.AnyOf {
		collectSchemaReferences(one, refs)
	}

	for _, one := range schemaDef.AllOf {
		collectSchemaReferences(one, refs)
	}

	for _, one := range schemaDef.OneOf {
		collectSchemaReferences(one, refs)
	}
}
