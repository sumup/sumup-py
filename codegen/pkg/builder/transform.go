package builder

import (
	"fmt"
	"log/slog"
	"slices"
	"strings"

	"github.com/iancoleman/strcase"
	"github.com/pb33f/libopenapi/datamodel/high/base"
	v3 "github.com/pb33f/libopenapi/datamodel/high/v3"
	"github.com/pb33f/libopenapi/orderedmap"

	"github.com/sumup/sumup-py/codegen/internal/stringx"
)

// schemasToTypes converts openapi3 schemas to golang struct and enum types.
func (b *Builder) schemasToTypes(schemas []*base.SchemaProxy) []Writable {
	var allTypes []Writable

	for _, s := range schemas {
		name := strcase.ToCamel(strings.TrimPrefix(s.GetReference(), "#/components/schemas/"))
		typeTpl := b.generateSchemaComponents(name, s.Schema())
		allTypes = append(allTypes, typeTpl...)
	}

	return allTypes
}

// TODO: is this different from respToTypes?
func (b *Builder) pathsToBodyTypes(paths *v3.Paths) []Writable {
	if paths == nil {
		return nil
	}

	paramTypes := make([]Writable, 0)
	for _, pathSpec := range paths.PathItems.FromOldest() {
		for _, opSpec := range pathSpec.GetOperations().FromOldest() {
			operationName := strcase.ToCamel(opSpec.OperationId)

			if opSpec.RequestBody != nil {
				mt, ok := opSpec.RequestBody.Content.Get("application/json")
				if ok && mt.Schema != nil {
					name := operationName + "Body"
					bodyObject, additionalTypes := b.createObject(mt.Schema.Schema(), name)
					paramTypes = append(paramTypes, additionalTypes...)
					paramTypes = append(paramTypes, bodyObject)
				}
			}
		}
	}

	return paramTypes
}

// constructParamTypes constructs struct for query parameters for an operation.
func (b *Builder) pathsToParamTypes(paths *v3.Paths) []Writable {
	if paths == nil {
		return nil
	}

	paramTypes := make([]Writable, 0)

	for _, pathSpec := range paths.PathItems.FromOldest() {
		for _, opSpec := range pathSpec.GetOperations().FromOldest() {
			operationName := strcase.ToCamel(opSpec.OperationId)

			if len(opSpec.Parameters) > 0 {
				fields := make([]Property, 0)
				for _, p := range opSpec.Parameters {
					// path parameters are passed as a parameters to the generated method
					if p.In == "path" || p.In == "header" {
						continue
					}

					name := p.Name
					alias := name
					if p.GoLow().IsReference() {
						name = strcase.ToCamel(strings.TrimPrefix(p.Schema.GetReference(), "#/components/schemas/"))
					}

					// NOTE: we should leave it as-is, but that doesn't work with 'include[]'
					name = strings.ReplaceAll(name, "[]", "")

					// NOTE: this also needs to be handled properly
					name = strings.ReplaceAll(name, ".", "_")

					typ := b.convertToValidPyType("", p.Schema)

					fields = append(fields, Property{
						Name:           name,
						SerializedName: alias,
						Type:           typ,
						Optional:       p.Required == nil || !*p.Required,
						Comment:        parameterPropertyDoc(p.Schema.Schema()),
					})
				}

				if len(fields) != 0 {
					paramsTypeName := operationName + "Params"
					paramsTpl := ClassDeclaration{
						Type:        "struct",
						Name:        paramsTypeName,
						Description: operationParamsDoc(paramsTypeName, opSpec),
						Fields:      fields,
					}

					paramTypes = append(paramTypes, &paramsTpl)
				}
			}
		}
	}

	return paramTypes
}

// pathsToResponseTypes generates response types for operations. This is responsible only for inlined
// schemas that are specific to the operation itself and are not references.
func (b *Builder) pathsToResponseTypes(paths *v3.Paths) []Writable {
	if paths == nil {
		return nil
	}

	responseTypes := make([]Writable, 0)
	for _, pathSpec := range paths.PathItems.FromOldest() {
		for _, opSpec := range pathSpec.GetOperations().FromOldest() {
			operationName := strcase.ToCamel(opSpec.OperationId)

			var successResponses []string
			for code, response := range opSpec.Responses.Codes.FromOldest() {
				isSuccess := strings.HasPrefix(code, "2")
				if !isSuccess {
					continue
				}

				if response.Content == nil {
					continue
				}

				content, ok := response.Content.Get("application/json")
				if !ok {
					continue
				}

				if content.Schema == nil {
					continue
				}

				if content.Schema.IsReference() {
					name := strcase.ToCamel(strings.TrimPrefix(content.Schema.GetReference(), "#/components/schemas/"))
					successResponses = append(successResponses, name)
					// schemas are handled separately, here we only care about inline schemas in the operation
					continue
				}

				name := b.getResponseName(operationName, code, content)

				objects := b.generateSchemaComponents(name, content.Schema.Schema())
				responseTypes = append(responseTypes, objects...)

				if strings.HasPrefix(code, "2") {
					if resp, ok := objects[len(objects)-1].(*ClassDeclaration); ok {
						successResponses = append(successResponses, resp.Name)
					} else if resp, ok := objects[len(objects)-1].(*TypeAlias); ok {
						successResponses = append(successResponses, resp.Name)
					}
				}
			}

			// if there are multiple success responses, we need to create a oneOf type
			if len(successResponses) > 1 {
				responseTypes = append(responseTypes, &OneOfDeclaration{
					Name:    operationName + "Response",
					Options: successResponses,
				})
			}
		}
	}

	return responseTypes
}

// generateSchemaComponents generates types from schema reference.
// This should be used to generate top-level types, that is - named schemas that are listed
// in `#/components/schemas/` part of the OpenAPI specs.
func (b *Builder) generateSchemaComponents(name string, spec *base.Schema) []Writable {
	types := make([]Writable, 0)

	switch {
	case len(spec.Enum) > 0:
		enum := createEnum(spec, name)
		if enum != nil {
			types = append(types, enum)
		}
	case slices.Contains(spec.Type, "string"):
		types = append(types, &TypeAlias{
			Comment: schemaDoc(name, spec),
			Type:    "str",
			Name:    name,
		})
	case slices.Contains(spec.Type, "integer"):
		types = append(types, &TypeAlias{
			Comment: schemaDoc(name, spec),
			Type:    "int",
			Name:    name,
		})
	case slices.Contains(spec.Type, "number"):
		types = append(types, &TypeAlias{
			Comment: schemaDoc(name, spec),
			Type:    "float",
			Name:    name,
		})
	case slices.Contains(spec.Type, "boolean"):
		types = append(types, &TypeAlias{
			Comment: schemaDoc(name, spec),
			Type:    "bool",
			Name:    name,
		})
	case slices.Contains(spec.Type, "array"):
		typeName, itemTypes := b.genSchema(spec.Items.A, stringx.MakeSingular(name))
		types = append(types, itemTypes...)
		types = append(types, &TypeAlias{
			Comment: schemaDoc(name, spec),
			Type:    fmt.Sprintf("list[%s]", typeName),
			Name:    name,
		})
	case slices.Contains(spec.Type, "object"):
		object, additionalTypes := b.createObject(spec, name)
		types = append(types, additionalTypes...)
		types = append(types, object)
	case spec.OneOf != nil:
		object := createOneOf(spec, name)
		types = append(types, object)
	case spec.AnyOf != nil:
		slog.Warn("AnyOf not supported, falling back to 'inteface{}'",
			slog.Any("name", name),
		)
		types = append(types, &ClassDeclaration{
			Description: schemaDoc(name, spec),
			Type:        "typing.Any",
			Name:        name,
		})
	case spec.AllOf != nil:
		object, additionalTypes := b.createAllOf(spec, name)
		types = append(types, additionalTypes...)
		types = append(types, object)
	default:
		if spec.Type != nil {
			slog.Warn("skipping unknown type",
				slog.Any("name", name),
				slog.Any("type", spec.Type),
			)
		}
	}

	return types
}

// genSchema is very similar to [generateSchemaComponents] but assumes that all schema components
// have been already generated.
func (b *Builder) genSchema(sp *base.SchemaProxy, name string) (string, []Writable) {
	if sp.GetReference() != "" {
		ref := strings.TrimPrefix(sp.GetReference(), "#/components/schemas/")
		if len(sp.Schema().Enum) > 0 {
			return strcase.ToCamel(stringx.MakeSingular(ref)), nil
		}

		return strcase.ToCamel(ref), nil
	}

	types := make([]Writable, 0)
	schema := sp.Schema()
	switch {
	case len(schema.Enum) > 0:
		enum := createEnum(schema, name)
		if enum != nil {
			types = append(types, enum)
		}
		return stringx.MakeSingular(name), types
	case slices.Contains(schema.Type, "string"):
		return formatStringType(schema), nil
	case slices.Contains(schema.Type, "integer"):
		return "int", nil
	case slices.Contains(schema.Type, "number"):
		return "float", nil
	case slices.Contains(schema.Type, "boolean"):
		return "bool", nil
	case slices.Contains(schema.Type, "array"):
		typeName, schemas := b.genSchema(schema.Items.A, stringx.MakeSingular(name))
		types = append(types, schemas...)
		return fmt.Sprintf("list[%s]", typeName), types
	case slices.Contains(schema.Type, "object"):
		object, additionalTypes := b.createObject(schema, name)
		types = append(types, additionalTypes...)
		types = append(types, object)
		return name, types
	case schema.OneOf != nil:
		object := createOneOf(schema, name)
		types = append(types, object)
		return name, types
	case schema.AnyOf != nil:
		slog.Warn("AnyOf not supported, falling back to 'any'",
			slog.Any("name", name),
		)
		return "typing.Any", nil
	case schema.AllOf != nil:
		object, additionalTypes := b.createAllOf(schema, name)
		types = append(types, additionalTypes...)
		types = append(types, object)
		return name, types
	default:
		if schema.Type != nil {
			slog.Warn("skipping unknown type",
				slog.Any("name", name),
				slog.Any("type", schema.Type),
			)
		}
		return "typing.Any", nil
	}
}

// createObject converts openapi schema into golang object.
func (b *Builder) createObject(schema *base.Schema, name string) (Writable, []Writable) {
	if (schema.Properties == nil || schema.Properties.Len() == 0) &&
		schema.AdditionalProperties != nil &&
		((schema.AdditionalProperties.IsB() && schema.AdditionalProperties.B) ||
			(schema.AdditionalProperties.IsA())) {

		return &TypeAlias{
			Comment: schemaDoc(name, schema),
			Name:    name,
			Type:    "dict[typing.Any, typing.Any]",
		}, nil
	}

	fields, additionalTypes := b.createFields(schema.Properties, name, schema.Required)
	return &ClassDeclaration{
		Description: schemaDoc(name, schema),
		Name:        name,
		Type:        "class",
		Fields:      fields,
	}, additionalTypes
}

// createFields returns list of fields for openapi schema properties.
func (b *Builder) createFields(properties *orderedmap.Map[string, *base.SchemaProxy], name string, required []string) ([]Property, []Writable) {
	fields := []Property{}
	types := []Writable{}

	for property, schema := range properties.FromOldest() {
		typeName, moreTypes := b.genSchema(schema, name+strcase.ToCamel(property))
		optional := !slices.Contains(required, property)
		fields = append(fields, Property{
			Name:     property,
			Type:     typeName,
			Comment:  schemaPropertyGodoc(schema.Schema()),
			Optional: optional,
		})
		types = append(types, moreTypes...)
	}

	return fields, types
}

func createEnum(schema *base.Schema, name string) Writable {
	enumName := stringx.MakeSingular(name)
	switch {
	case slices.Contains(schema.Type, "string"):
		values := make([]string, 0)
		for _, v := range schema.Enum {
			var val string
			if err := v.Decode(&val); err != nil {
				slog.Warn("invalid enum value",
					slog.String("enum", name),
					slog.String("expected", "string"),
					slog.String("got", fmt.Sprintf("%T", v)),
					slog.String("err", err.Error()),
					slog.Any("raw", v),
				)
				continue
			}
			values = append(values, val)
		}

		return &EnumDeclaration[string]{
			Comment: schemaDoc(name, schema),
			Name:    enumName,
			Type:    "string",
			Values:  values,
		}
	case slices.Contains(schema.Type, "integer"):
		if schema.Format == "int64" {
			values := make([]int64, 0)
			for _, v := range schema.Enum {
				var val float64
				if err := v.Decode(&val); err != nil {
					slog.Warn("invalid enum value",
						slog.String("enum", name),
						slog.String("expected", "string"),
						slog.String("err", err.Error()),
						slog.String("got", fmt.Sprintf("%T", v)),
					)
					continue
				}
				values = append(values, int64(val))
			}

			return &EnumDeclaration[int64]{
				Comment: schemaDoc(name, schema),
				Name:    stringx.MakeSingular(name),
				Type:    "int64",
				Values:  values,
			}
		}

		values := make([]int, 0)
		for _, v := range schema.Enum {
			var val float64
			if err := v.Decode(&val); err != nil {
				slog.Warn("invalid enum value",
					slog.String("enum", name),
					slog.String("expected", "string"),
					slog.String("err", err.Error()),
					slog.String("got", fmt.Sprintf("%T", v)),
				)
				continue
			}
			values = append(values, int(val))
		}

		return &EnumDeclaration[int]{
			Comment: schemaDoc(name, schema),
			Name:    stringx.MakeSingular(name),
			Type:    "int",
			Values:  values,
		}
	case slices.Contains(schema.Type, "number"):
		values := make([]float64, 0)
		for _, v := range schema.Enum {
			var val float64
			if err := v.Decode(&val); err != nil {
				slog.Warn("invalid enum value",
					slog.String("enum", name),
					slog.String("expected", "string"),
					slog.String("err", err.Error()),
					slog.String("got", fmt.Sprintf("%T", v)),
				)
				continue
			}
			values = append(values, val)
		}

		return &EnumDeclaration[float64]{
			Comment: schemaDoc(name, schema),
			Name:    stringx.MakeSingular(name),
			Type:    "float",
			Values:  values,
		}
	default:
		return nil
	}
}

// createAllOf creates a type declaration for `allOf` schema.
func (b *Builder) createAllOf(schema *base.Schema, name string) (*ClassDeclaration, []Writable) {
	types := []Writable{}
	var fields []Property
	var seen []string
	for _, s := range schema.AllOf {
		// Solve collision between the properties of `allOf` before we pass it further to avoid
		// generating nested objects and enums multiple times.
		properties := s.Schema().Properties
		for _, f := range seen {
			properties.Delete(f)
		}

		objectFields, additionalTypes := b.createFields(properties, name, s.Schema().Required)
		types = append(types, additionalTypes...)
		fields = append(fields, objectFields...)

		seen = append(seen, slices.Collect(properties.KeysFromOldest())...)
	}

	return &ClassDeclaration{
		Description: schemaDoc(name, schema),
		Name:        name,
		Type:        "struct",
		Fields:      uniqueFields(fields),
	}, types
}

// createOneOf creates a type declaration for `oneOf` schema.
func createOneOf(schema *base.Schema, name string) *ClassDeclaration {
	// TODO: implement `func (v *{{name}}) AsXXX() (XXX, error) { ... }`
	// that allows converting one of from `json.RawMessage` to possible variants.

	return &ClassDeclaration{
		Description: schemaDoc(name, schema),
		Name:        name,
		Type:        "json.RawMessage",
	}
}

func uniqueFields(fields []Property) []Property {
	return uniqueFunc(fields, func(f Property) string { return f.Name })
}

func uniqueFunc[T any, C comparable](arr []T, keyFn func(T) C) []T {
	seen := make(map[C]bool)

	n := 0
	for _, ele := range arr {
		key := keyFn(ele)
		if ok := seen[key]; ok {
			continue
		}
		arr[n] = ele
		n++
		seen[key] = true
	}

	return arr[:n]
}

func (b *Builder) getResponseName(operationName, responseCode string, content *v3.MediaType) string {
	schema := content.Schema.Schema()
	if schema != nil && schema.Title != "" {
		return operationName + strcase.ToCamel(content.Schema.Schema().Title) + "Response"
	}

	return operationName + responseCode + "Response"
}
