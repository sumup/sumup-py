package builder

import (
	"fmt"
	"slices"
	"strconv"
	"strings"

	"github.com/iancoleman/strcase"
	"github.com/pb33f/libopenapi/datamodel/high/base"
	v3 "github.com/pb33f/libopenapi/datamodel/high/v3"
	"github.com/pb33f/libopenapi/orderedmap"
	"go.yaml.in/yaml/v4"
)

const (
	sampleCatalogSchemaVersion = 1
	sdkPackage                 = "sumup"
)

// SampleCatalog is the versioned JSON contract consumed by documentation sites.
type SampleCatalog struct {
	SchemaVersion  int      `json:"schemaVersion"`
	Language       string   `json:"language"`
	SDK            SDK      `json:"sdk"`
	OpenAPIVersion string   `json:"openAPIVersion"`
	Samples        []Sample `json:"samples"`
}

// SDK identifies the package used by every generated sample.
type SDK struct {
	Module  string `json:"module"`
	Version string `json:"version"`
}

// Sample is a complete Python program for one OpenAPI operation example.
type Sample struct {
	ID          string `json:"id"`
	OperationID string `json:"operationId"`
	Example     string `json:"example,omitempty"`
	Summary     string `json:"summary,omitempty"`
	Description string `json:"description,omitempty"`
	HTTPMethod  string `json:"httpMethod"`
	Path        string `json:"path"`
	Source      string `json:"sample"`
}

// Samples builds a deterministic catalog of Python examples using the generated SDK method IR.
func (b *Builder) Samples(sdkVersion string) (*SampleCatalog, error) {
	if b.spec == nil {
		return nil, fmt.Errorf("missing specs: call Load to load the specs first")
	}
	if b.spec.Info == nil {
		return nil, fmt.Errorf("missing specs info: call Load to load the specs first")
	}

	paths := slices.Collect(b.spec.Paths.PathItems.KeysFromOldest())
	slices.Sort(paths)
	samples := make([]Sample, 0)
	for _, apiPath := range paths {
		pathItem, ok := b.spec.Paths.PathItems.Get(apiPath)
		if !ok || pathItem == nil || pathItem.IsReference() {
			continue
		}

		operations := pathItem.GetOperations()
		methods := slices.Collect(operations.KeysFromOldest())
		slices.Sort(methods)
		for _, httpMethod := range methods {
			operation, ok := operations.Get(httpMethod)
			if !ok || operation == nil {
				continue
			}
			if operation.OperationId == "" {
				return nil, fmt.Errorf("missing operation id for %s %s", strings.ToUpper(httpMethod), apiPath)
			}

			operationCopy := *operation
			operationCopy.Parameters = append(slices.Clone(operation.Parameters), pathItem.Parameters...)
			method, err := b.operationToMethod(httpMethod, apiPath, &operationCopy)
			if err != nil {
				return nil, fmt.Errorf("build operation %q: %w", operation.OperationId, err)
			}

			tagName := "shared"
			if len(operation.Tags) > 0 {
				tagName = strings.ToLower(operation.Tags[0])
			}
			if pathsForTag := b.pathsByTag[tagName]; pathsForTag != nil {
				flattenMethodBodies([]*Method{method}, b.pathsToBodyTypes(pathsForTag))
			}

			operationSamples, err := b.samplesForOperation(
				tagName,
				strings.ToUpper(httpMethod),
				apiPath,
				&operationCopy,
				method,
			)
			if err != nil {
				return nil, fmt.Errorf("generate samples for %q: %w", operation.OperationId, err)
			}
			samples = append(samples, operationSamples...)
		}
	}

	slices.SortFunc(samples, func(a, b Sample) int {
		return strings.Compare(a.ID, b.ID)
	})

	return &SampleCatalog{
		SchemaVersion: sampleCatalogSchemaVersion,
		Language:      "python",
		SDK: SDK{
			Module:  sdkPackage,
			Version: sdkVersion,
		},
		OpenAPIVersion: strings.TrimSpace(b.spec.Info.Version),
		Samples:        samples,
	}, nil
}

type requestExample struct {
	name        string
	summary     string
	description string
	value       any
	provided    bool
}

func (b *Builder) samplesForOperation(
	tagName string,
	httpMethod string,
	apiPath string,
	operation *v3.Operation,
	method *Method,
) ([]Sample, error) {
	examples := requestExamples(operation)
	samples := make([]Sample, 0, len(examples))
	for _, example := range examples {
		source, err := b.renderSample(tagName, operation, method, example)
		if err != nil {
			return nil, err
		}

		id := operation.OperationId
		if example.name != "" {
			id += "." + example.name
		}
		summary := strings.TrimSpace(operation.Summary)
		if example.summary != "" {
			summary = strings.TrimSpace(example.summary)
		}
		description := strings.TrimSpace(operation.Description)
		if example.description != "" {
			description = strings.TrimSpace(example.description)
		}

		samples = append(samples, Sample{
			ID:          id,
			OperationID: operation.OperationId,
			Example:     example.name,
			Summary:     summary,
			Description: description,
			HTTPMethod:  httpMethod,
			Path:        apiPath,
			Source:      source,
		})
	}

	return samples, nil
}

func requestExamples(operation *v3.Operation) []requestExample {
	mediaType, ok := requestJSONMediaType(operation)
	if !ok {
		return []requestExample{{}}
	}

	if mediaType.Examples != nil && mediaType.Examples.Len() > 0 {
		names := slices.Collect(mediaType.Examples.KeysFromOldest())
		slices.Sort(names)
		examples := make([]requestExample, 0, len(names))
		for _, name := range names {
			example, ok := mediaType.Examples.Get(name)
			if !ok || example == nil {
				continue
			}
			value, provided := decodeSampleNode(example.Value)
			examples = append(examples, requestExample{
				name:        name,
				summary:     example.Summary,
				description: example.Description,
				value:       value,
				provided:    provided,
			})
		}
		if len(examples) > 0 {
			return examples
		}
	}

	if value, provided := decodeSampleNode(mediaType.Example); provided {
		return []requestExample{{value: value, provided: true}}
	}
	if value, provided := sampleSchemaExample(mediaType.Schema); provided {
		return []requestExample{{value: value, provided: true}}
	}

	return []requestExample{{}}
}

type sampleArgument struct {
	name  string
	value any
}

func (b *Builder) renderSample(
	tagName string,
	operation *v3.Operation,
	method *Method,
	example requestExample,
) (string, error) {
	arguments := make([]sampleArgument, 0)
	for _, pathParameter := range method.PathParams {
		parameter := operationParameter(operation.Parameters, pathParameter.Name, "path")
		value, provided := sampleParameterValue(parameter)
		arguments = append(arguments, sampleArgument{
			value: sampleValue(parameterSchema(parameter), value, provided),
		})
	}

	if method.HasFlattenedBody() {
		values, _ := example.value.(map[string]any)
		for _, field := range method.BodyFields {
			if sampleSchemaReadOnly(field.Schema) {
				continue
			}
			key := field.WireName()
			value, provided := values[key]
			if !provided && (!example.provided || !field.Optional) {
				value, provided = sampleSchemaExample(field.Schema)
			}
			if field.Optional && !provided {
				continue
			}
			arguments = append(arguments, sampleArgument{
				name:  field.FieldName(),
				value: sampleValue(field.Schema, value, provided),
			})
		}
	} else if method.HasBody {
		mediaType, _ := requestJSONMediaType(operation)
		arguments = append(arguments, sampleArgument{
			value: sampleValue(mediaType.Schema, example.value, example.provided),
		})
	}

	for _, field := range method.QueryFields {
		parameter := operationParameter(operation.Parameters, field.WireName(), "query")
		value, provided := sampleParameterValue(parameter)
		if field.Optional && !provided {
			continue
		}
		arguments = append(arguments, sampleArgument{
			name:  field.FieldName(),
			value: sampleValue(field.Schema, value, provided),
		})
	}

	resourceName := strcase.ToSnake(tagName)
	var source strings.Builder
	source.WriteString("import os\n\n")
	source.WriteString("import sumup\n\n")
	source.WriteString("client = sumup.Sumup(api_key=os.environ[\"SUMUP_API_KEY\"])\n")
	if method.ResponseType != nil {
		source.WriteString("result = ")
	}
	fmt.Fprintf(&source, "client.%s.%s(", resourceName, method.FunctionName)
	if len(arguments) == 0 {
		source.WriteString(")\n")
	} else {
		source.WriteString("\n")
	}
	for _, argument := range arguments {
		source.WriteString("    ")
		if argument.name != "" {
			fmt.Fprintf(&source, "%s=", argument.name)
		}
		source.WriteString(renderPythonValue(argument.value, "    "))
		source.WriteString(",\n")
	}
	if len(arguments) > 0 {
		source.WriteString(")\n")
	}
	if method.ResponseType != nil {
		source.WriteString("print(result)\n")
	}

	return source.String(), nil
}

func requestJSONMediaType(operation *v3.Operation) (*v3.MediaType, bool) {
	if operation == nil || operation.RequestBody == nil {
		return nil, false
	}
	return jsonMediaType(operation.RequestBody.Content)
}

func jsonMediaType(content *orderedmap.Map[string, *v3.MediaType]) (*v3.MediaType, bool) {
	if content == nil {
		return nil, false
	}
	if mediaType, ok := content.Get("application/json"); ok && mediaType != nil {
		return mediaType, true
	}
	for contentType, mediaType := range content.FromOldest() {
		if strings.HasSuffix(contentType, "+json") && mediaType != nil {
			return mediaType, true
		}
	}
	return nil, false
}

func operationParameter(parameters []*v3.Parameter, name, location string) *v3.Parameter {
	for _, parameter := range parameters {
		if parameter != nil && parameter.Name == name && parameter.In == location {
			return parameter
		}
	}
	return nil
}

func parameterSchema(parameter *v3.Parameter) *base.SchemaProxy {
	if parameter == nil {
		return nil
	}
	return parameter.Schema
}

func sampleParameterValue(parameter *v3.Parameter) (any, bool) {
	if parameter == nil {
		return nil, false
	}
	if value, ok := decodeSampleNode(parameter.Example); ok {
		return value, true
	}
	if parameter.Examples != nil {
		names := slices.Collect(parameter.Examples.KeysFromOldest())
		slices.Sort(names)
		for _, name := range names {
			example, ok := parameter.Examples.Get(name)
			if ok && example != nil {
				if value, ok := decodeSampleNode(example.Value); ok {
					return value, true
				}
			}
		}
	}
	return sampleSchemaExample(parameter.Schema)
}

func sampleSchemaExample(schema *base.SchemaProxy) (any, bool) {
	if schema == nil || schema.Schema() == nil {
		return nil, false
	}
	spec := schema.Schema()
	if value, ok := decodeSampleNode(spec.Example); ok {
		return value, true
	}
	for _, example := range spec.Examples {
		if value, ok := decodeSampleNode(example); ok {
			return value, true
		}
	}
	if value, ok := decodeSampleNode(spec.Default); ok {
		return value, true
	}
	if len(spec.Enum) > 0 {
		return decodeSampleNode(spec.Enum[0])
	}
	return nil, false
}

func decodeSampleNode(node *yaml.Node) (any, bool) {
	if node == nil {
		return nil, false
	}
	var value any
	if err := node.Decode(&value); err != nil {
		return nil, false
	}
	return value, true
}

func sampleValue(schema *base.SchemaProxy, raw any, provided bool) any {
	return sampleValueAtDepth(schema, raw, provided, 0)
}

func sampleValueAtDepth(schema *base.SchemaProxy, raw any, provided bool, depth int) any {
	if provided {
		return raw
	}
	if value, ok := sampleSchemaExample(schema); ok {
		return value
	}
	if schema == nil || schema.Schema() == nil {
		return "value"
	}
	return fallbackSampleValue(schema.Schema(), depth)
}

func fallbackSampleValue(schema *base.Schema, depth int) any {
	if schema == nil || depth > 8 {
		return map[string]any{}
	}

	if len(schema.AllOf) > 0 {
		result := make(map[string]any)
		for _, part := range schema.AllOf {
			value := sampleValueAtDepth(part, nil, false, depth+1)
			if fields, ok := value.(map[string]any); ok {
				for key, field := range fields {
					result[key] = field
				}
			}
		}
		return result
	}
	if len(schema.OneOf) > 0 {
		return sampleValueAtDepth(schema.OneOf[0], nil, false, depth+1)
	}
	if len(schema.AnyOf) > 0 {
		return sampleValueAtDepth(schema.AnyOf[0], nil, false, depth+1)
	}

	switch {
	case slices.Contains(schema.Type, "object") || schema.Properties != nil:
		value := make(map[string]any)
		if schema.Properties != nil {
			for _, name := range schema.Required {
				property, ok := schema.Properties.Get(name)
				if ok && !sampleSchemaReadOnly(property) {
					if example, provided := sampleSchemaExample(property); provided {
						value[name] = example
					} else if property != nil && property.Schema() != nil {
						value[name] = fallbackSampleValue(property.Schema(), depth+1)
					}
				}
			}
		}
		return value
	case slices.Contains(schema.Type, "array"):
		return []any{}
	case slices.Contains(schema.Type, "boolean"):
		return true
	case slices.Contains(schema.Type, "integer"):
		return 1
	case slices.Contains(schema.Type, "number"):
		return 1.0
	case slices.Contains(schema.Type, "string"):
		switch schema.Format {
		case "date-time":
			return "2025-01-01T00:00:00Z"
		case "date":
			return "2025-01-01"
		case "time":
			return "12:00:00"
		case "email":
			return "developer@example.com"
		case "uri", "url":
			return "https://example.com"
		case "uuid":
			return "00000000-0000-0000-0000-000000000000"
		default:
			return "string"
		}
	default:
		return map[string]any{}
	}
}

func sampleSchemaReadOnly(schema *base.SchemaProxy) bool {
	return schema != nil && schema.Schema() != nil && schema.Schema().ReadOnly != nil && *schema.Schema().ReadOnly
}

func renderPythonValue(value any, indent string) string {
	switch typed := value.(type) {
	case map[string]any:
		if len(typed) == 0 {
			return "{}"
		}
		keys := make([]string, 0, len(typed))
		for key := range typed {
			keys = append(keys, key)
		}
		slices.Sort(keys)
		var out strings.Builder
		out.WriteString("{\n")
		for _, key := range keys {
			fmt.Fprintf(&out, "%s    %s: %s,\n", indent, strconv.Quote(key), renderPythonValue(typed[key], indent+"    "))
		}
		out.WriteString(indent)
		out.WriteString("}")
		return out.String()
	case []any:
		if len(typed) == 0 {
			return "[]"
		}
		var out strings.Builder
		out.WriteString("[\n")
		for _, item := range typed {
			fmt.Fprintf(&out, "%s    %s,\n", indent, renderPythonValue(item, indent+"    "))
		}
		out.WriteString(indent)
		out.WriteString("]")
		return out.String()
	case string:
		return strconv.Quote(typed)
	case bool:
		if typed {
			return "True"
		}
		return "False"
	case nil:
		return "None"
	case int:
		return strconv.Itoa(typed)
	case int8:
		return strconv.FormatInt(int64(typed), 10)
	case int16:
		return strconv.FormatInt(int64(typed), 10)
	case int32:
		return strconv.FormatInt(int64(typed), 10)
	case int64:
		return strconv.FormatInt(typed, 10)
	case uint:
		return strconv.FormatUint(uint64(typed), 10)
	case uint8:
		return strconv.FormatUint(uint64(typed), 10)
	case uint16:
		return strconv.FormatUint(uint64(typed), 10)
	case uint32:
		return strconv.FormatUint(uint64(typed), 10)
	case uint64:
		return strconv.FormatUint(typed, 10)
	case float32:
		return strconv.FormatFloat(float64(typed), 'f', -1, 32)
	case float64:
		return strconv.FormatFloat(typed, 'f', -1, 64)
	default:
		return strconv.Quote(fmt.Sprint(typed))
	}
}
