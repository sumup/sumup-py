package builder

import (
	"fmt"
	"slices"
	"sort"
	"strconv"
	"strings"

	"github.com/iancoleman/strcase"
	"github.com/pb33f/libopenapi/datamodel/high/base"
	v3 "github.com/pb33f/libopenapi/datamodel/high/v3"
	"github.com/pb33f/libopenapi/orderedmap"
	"go.yaml.in/yaml/v4"

	"github.com/sumup/sumup-py/codegen/pkg/extension"
)

type OperationSample struct {
	Sample string `json:"sample"`
}

type sampleTypeInfo struct {
	Package string
	Name    string
}

func (t sampleTypeInfo) QualifiedName() string {
	if t.Package == "" || t.Name == "" {
		return ""
	}
	return fmt.Sprintf("sumup.%s.%s", t.Package, t.Name)
}

func (b *Builder) BuildSamples() (map[string]map[string]OperationSample, error) {
	if b.spec == nil {
		return nil, fmt.Errorf("missing specs: call Load to load the specs first")
	}

	samples := make(map[string]map[string]OperationSample)
	for path, pathItem := range b.spec.Paths.PathItems.FromOldest() {
		if pathItem == nil || pathItem.IsReference() {
			continue
		}

		methodSamples, err := b.pathToSamples(pathItem)
		if err != nil {
			return nil, fmt.Errorf("build samples for %s: %w", path, err)
		}
		if len(methodSamples) == 0 {
			continue
		}

		samples[path] = methodSamples
	}

	return samples, nil
}

func (b *Builder) pathToSamples(pathItem *v3.PathItem) (map[string]OperationSample, error) {
	methods := pathItem.GetOperations()
	keys := make([]string, 0, methods.Len())
	for key := range methods.KeysFromOldest() {
		keys = append(keys, key)
	}
	sort.Strings(keys)

	out := make(map[string]OperationSample, len(keys))
	for _, key := range keys {
		op, ok := methods.Get(key)
		if !ok {
			continue
		}

		sample, err := b.operationSample(pathItem.Parameters, op)
		if err != nil {
			return nil, err
		}
		out[strings.ToUpper(key)] = OperationSample{Sample: sample}
	}

	return out, nil
}

func (b *Builder) operationSample(pathItemParams []*v3.Parameter, op *v3.Operation) (string, error) {
	tagName := "shared"
	switch {
	case len(op.Tags) > 1:
		tagName = strings.ToLower(op.Tags[0])
	case len(op.Tags) == 1:
		tagName = strings.ToLower(op.Tags[0])
	}

	tag := b.tagByTagName(tagName)
	resourcePackage := strcase.ToSnake(tag.Name)
	if resourcePackage == "" {
		resourcePackage = tagName
	}

	methodName := sampleMethodName(op)
	args := make([]string, 0)
	usesDatetime := false

	params := append(slices.Clone(pathItemParams), op.Parameters...)
	for _, parameter := range params {
		param := b.resolveParameter(parameter)
		if param == nil || param.In != "path" {
			continue
		}

		expr, usesDT, err := b.sampleExprForSchema(sampleTypeInfo{}, param.Schema, sampleValueFromParameter(param), 0, sampleOptions{})
		if err != nil {
			return "", err
		}
		args = append(args, fmt.Sprintf("%s=%s", strcase.ToSnake(param.Name), expr))
		usesDatetime = usesDatetime || usesDT
	}

	if body := operationJSONRequestBody(op); body != nil && body.Schema != nil {
		bodyExpr, usesDT, err := b.sampleExprForSchema(
			sampleTypeInfo{Package: resourcePackage, Name: strcase.ToCamel(op.OperationId) + "Body"},
			body.Schema,
			sampleValueFromMediaType(body),
			0,
			sampleOptions{Mode: sampleModeBody},
		)
		if err != nil {
			return "", err
		}
		args = append(args, "body="+bodyExpr)
		usesDatetime = usesDatetime || usesDT
	}

	queryParams := nonPathParameters(b, params)
	if len(queryParams) > 0 {
		queryExpr, usesDT, err := b.sampleExprForQueryParams(
			sampleTypeInfo{Package: resourcePackage, Name: strcase.ToCamel(op.OperationId) + "Params"},
			queryParams,
		)
		if err != nil {
			return "", err
		}
		if queryExpr != "" {
			args = append(args, "params="+queryExpr)
			usesDatetime = usesDatetime || usesDT
		}
	}

	assign := ""
	respType, err := b.getSuccessResponseType(op)
	if err != nil {
		return "", err
	}
	if respType != nil {
		assign = "result = "
	}

	imports := []string{"import sumup"}
	if usesDatetime {
		imports = append(imports, "import datetime")
	}

	var out strings.Builder
	out.WriteString(strings.Join(imports, "\n"))
	out.WriteString("\n\nclient = sumup.Sumup()\n\n")
	out.WriteString(assign)
	out.WriteString("client.")
	out.WriteString(resourcePackage)
	out.WriteString(".")
	out.WriteString(methodName)
	out.WriteString("(\n")
	for _, arg := range args {
		out.WriteString(indentPython(arg, 1))
		out.WriteString(",\n")
	}
	out.WriteString(")")

	return out.String(), nil
}

func sampleMethodName(op *v3.Operation) string {
	methodName := strcase.ToSnake(op.OperationId)
	if ext, ok := extension.Get[map[string]any](op.Extensions, "x-codegen"); ok {
		if name, ok := ext["method_name"]; ok {
			if nameStr, ok := name.(string); ok {
				methodName = strcase.ToSnake(nameStr)
			}
		}
	}
	return methodName
}

func (b *Builder) resolveParameter(param *v3.Parameter) *v3.Parameter {
	if param == nil || !param.IsReference() {
		return param
	}
	if b.spec == nil || b.spec.Components == nil || b.spec.Components.Parameters == nil {
		return nil
	}

	name := strings.TrimPrefix(param.GetReference(), "#/components/parameters/")
	resolved, ok := b.spec.Components.Parameters.Get(name)
	if !ok {
		return nil
	}
	return resolved
}

func nonPathParameters(b *Builder, params []*v3.Parameter) []*v3.Parameter {
	queryParams := make([]*v3.Parameter, 0)
	for _, p := range params {
		param := b.resolveParameter(p)
		if param == nil || param.In == "path" || param.In == "header" {
			continue
		}
		queryParams = append(queryParams, param)
	}
	return queryParams
}

func operationJSONRequestBody(op *v3.Operation) *v3.MediaType {
	if op == nil || op.RequestBody == nil || op.RequestBody.Content == nil {
		return nil
	}

	mt, ok := op.RequestBody.Content.Get("application/json")
	if ok && mt != nil {
		return mt
	}
	return nil
}

type sampleMode uint8

const (
	sampleModeGeneric sampleMode = iota
	sampleModeBody
	sampleModeQuery
)

type sampleOptions struct {
	Mode sampleMode
}

func (b *Builder) sampleExprForQueryParams(typeInfo sampleTypeInfo, params []*v3.Parameter) (string, bool, error) {
	if len(params) == 0 {
		return "", false, nil
	}

	lines := make([]string, 0, len(params))
	usesDatetime := false
	for _, param := range params {
		example := sampleValueFromParameter(param)
		hasExample := example != nil
		include := param.Required != nil && *param.Required
		if !include && hasExample {
			include = true
		}
		if !include {
			continue
		}

		expr, usesDT, err := b.sampleExprForSchema(sampleTypeInfo{}, param.Schema, example, 1, sampleOptions{Mode: sampleModeQuery})
		if err != nil {
			return "", false, err
		}
		lines = append(lines, fmt.Sprintf("%s=%s", pythonFieldName(parameterFieldName(param.Name)), expr))
		usesDatetime = usesDatetime || usesDT
	}

	if len(lines) == 0 {
		param := params[0]
		expr, usesDT, err := b.sampleExprForSchema(sampleTypeInfo{}, param.Schema, nil, 1, sampleOptions{Mode: sampleModeQuery})
		if err != nil {
			return "", false, err
		}
		lines = append(lines, fmt.Sprintf("%s=%s", pythonFieldName(parameterFieldName(param.Name)), expr))
		usesDatetime = usesDatetime || usesDT
	}

	return renderCall(typeInfo.QualifiedName(), lines, 0), usesDatetime, nil
}

func (b *Builder) sampleExprForSchema(typeInfo sampleTypeInfo, schema *base.SchemaProxy, example any, level int, opts sampleOptions) (string, bool, error) {
	if schema == nil {
		return "None", false, nil
	}

	if schema.GetReference() != "" {
		resolved := schema.Schema()
		if resolved == nil {
			return "None", false, nil
		}
		refName := b.getReferenceSchema(schema)
		if typeInfo.Name == "" {
			typeInfo.Name = refName
		}
		return b.sampleExprForResolvedSchema(typeInfo, resolved, example, level, opts)
	}

	if schema.Schema() == nil {
		return "None", false, nil
	}
	return b.sampleExprForResolvedSchema(typeInfo, schema.Schema(), example, level, opts)
}

func (b *Builder) sampleExprForResolvedSchema(typeInfo sampleTypeInfo, schema *base.Schema, example any, level int, opts sampleOptions) (string, bool, error) {
	if schema == nil {
		return "None", false, nil
	}

	if example == nil {
		example, _ = sampleValueFromSchema(schema)
	}
	if example == nil && schema.Const != nil {
		example, _ = sampleValueFromYAMLNode(schema.Const)
	}
	if example == nil && len(schema.Enum) > 0 {
		example = sampleValueFromEnum(schema.Enum)
	}

	switch {
	case len(schema.OneOf) > 0:
		return b.sampleExprForSchema(typeInfo, schema.OneOf[0], example, level, opts)
	case schema.AllOf != nil:
		return b.sampleExprForAllOf(typeInfo, schema, example, level, opts)
	case slices.Contains(schema.Type, "object"):
		return b.sampleExprForObject(typeInfo, schema, example, level, opts)
	case slices.Contains(schema.Type, "array"):
		return b.sampleExprForArray(typeInfo, schema, example, level, opts)
	case slices.Contains(schema.Type, "string"):
		return sampleStringExpr(schema, example)
	case slices.Contains(schema.Type, "integer"):
		return sampleIntegerExpr(example)
	case slices.Contains(schema.Type, "number"):
		return sampleNumberExpr(example)
	case slices.Contains(schema.Type, "boolean"):
		return sampleBoolExpr(example)
	default:
		if schema.AdditionalProperties != nil && schema.AdditionalProperties.IsA() {
			if m, ok := example.(map[string]any); ok && len(m) > 0 {
				return renderDictLiteral(m), false, nil
			}
			return `{"key": "value"}`, false, nil
		}
	}

	return `None`, false, nil
}

func (b *Builder) sampleExprForAllOf(typeInfo sampleTypeInfo, schema *base.Schema, example any, level int, opts sampleOptions) (string, bool, error) {
	type fieldSample struct {
		name         string
		expr         string
		usesDatetime bool
	}

	exampleMap, _ := example.(map[string]any)
	fields := make([]fieldSample, 0)
	seen := make(map[string]struct{})

	for _, part := range schema.AllOf {
		if part == nil || part.Schema() == nil {
			continue
		}
		partSchema := part.Schema()
		properties := orderedPropertyNames(partSchema.Properties)
		required := requiredPropertySet(partSchema.Required)
		for _, property := range properties {
			if _, ok := seen[property]; ok {
				continue
			}
			seen[property] = struct{}{}

			propSchema, ok := partSchema.Properties.Get(property)
			if !ok {
				continue
			}

			value, hasValue := exampleMap[property]
			include := required[property]
			if opts.Mode == sampleModeQuery {
				include = include || hasValue || schemaProxyHasExplicitExample(propSchema)
			} else if !hasValue {
				include = include || (len(required) == 0 && schemaProxyHasExplicitExample(propSchema))
			}
			if !include {
				continue
			}

			fieldType := b.sampleFieldType(typeInfo, property, propSchema)
			expr, usesDT, err := b.sampleExprForSchema(fieldType, propSchema, value, level+1, sampleOptions{})
			if err != nil {
				return "", false, err
			}
			fields = append(fields, fieldSample{name: pythonFieldName(property), expr: expr, usesDatetime: usesDT})
		}
	}

	if len(fields) == 0 {
		return renderCall(typeInfo.QualifiedName(), []string{}, level), false, nil
	}

	args := make([]string, 0, len(fields))
	usesDatetime := false
	for _, field := range fields {
		args = append(args, fmt.Sprintf("%s=%s", field.name, field.expr))
		usesDatetime = usesDatetime || field.usesDatetime
	}

	return renderCall(typeInfo.QualifiedName(), args, level), usesDatetime, nil
}

func (b *Builder) sampleExprForObject(typeInfo sampleTypeInfo, schema *base.Schema, example any, level int, opts sampleOptions) (string, bool, error) {
	if schema.AdditionalProperties != nil && ((schema.AdditionalProperties.IsB() && schema.AdditionalProperties.B) || schema.AdditionalProperties.IsA()) && (schema.Properties == nil || schema.Properties.Len() == 0) {
		if m, ok := example.(map[string]any); ok && len(m) > 0 {
			return renderDictLiteral(m), false, nil
		}
		return `{"key": "value"}`, false, nil
	}
	if schema.Properties == nil || schema.Properties.Len() == 0 {
		if m, ok := example.(map[string]any); ok && len(m) > 0 {
			return renderDictLiteral(m), false, nil
		}
		return `{"key": "value"}`, false, nil
	}

	exampleMap, _ := example.(map[string]any)
	required := requiredPropertySet(schema.Required)
	properties := orderedPropertyNames(schema.Properties)

	args := make([]string, 0, len(properties))
	usesDatetime := false
	for _, property := range properties {
		propSchema, ok := schema.Properties.Get(property)
		if !ok {
			continue
		}

		value, hasValue := exampleMap[property]
		include := required[property]
		switch opts.Mode {
		case sampleModeQuery:
			include = include || hasValue || schemaProxyHasExplicitExample(propSchema)
		case sampleModeBody:
			if !include && len(required) == 0 {
				include = hasValue || schemaProxyHasExplicitExample(propSchema)
			}
		default:
			include = include || hasValue
		}
		if !include {
			continue
		}

		fieldType := b.sampleFieldType(typeInfo, property, propSchema)
		expr, usesDT, err := b.sampleExprForSchema(fieldType, propSchema, value, level+1, sampleOptions{})
		if err != nil {
			return "", false, err
		}
		args = append(args, fmt.Sprintf("%s=%s", pythonFieldName(property), expr))
		usesDatetime = usesDatetime || usesDT
	}

	if len(args) == 0 && len(properties) > 0 {
		property := properties[0]
		propSchema, _ := schema.Properties.Get(property)
		fieldType := b.sampleFieldType(typeInfo, property, propSchema)
		expr, usesDT, err := b.sampleExprForSchema(fieldType, propSchema, nil, level+1, sampleOptions{})
		if err != nil {
			return "", false, err
		}
		args = append(args, fmt.Sprintf("%s=%s", pythonFieldName(property), expr))
		usesDatetime = usesDatetime || usesDT
	}

	if qualified := typeInfo.QualifiedName(); qualified != "" {
		return renderCall(qualified, args, level), usesDatetime, nil
	}

	if m, ok := example.(map[string]any); ok && len(m) > 0 {
		return renderDictLiteral(m), usesDatetime, nil
	}
	return `{"key": "value"}`, usesDatetime, nil
}

func (b *Builder) sampleExprForArray(typeInfo sampleTypeInfo, schema *base.Schema, example any, level int, _ sampleOptions) (string, bool, error) {
	if schema.Items == nil || !schema.Items.IsA() || schema.Items.A == nil {
		return "[]", false, nil
	}

	var itemExample any
	if values, ok := example.([]any); ok && len(values) > 0 {
		itemExample = values[0]
	}

	itemType := b.sampleArrayItemType(typeInfo, schema.Items.A)
	itemExpr, usesDatetime, err := b.sampleExprForSchema(itemType, schema.Items.A, itemExample, level+1, sampleOptions{})
	if err != nil {
		return "", false, err
	}

	return renderListLiteral([]string{itemExpr}, level), usesDatetime, nil
}

func (b *Builder) sampleFieldType(parent sampleTypeInfo, property string, schema *base.SchemaProxy) sampleTypeInfo {
	if schema == nil {
		return sampleTypeInfo{}
	}
	if schema.GetReference() != "" {
		return sampleTypeInfo{
			Package: parent.Package,
			Name:    b.getReferenceSchema(schema),
		}
	}
	if schema.Schema() == nil {
		return sampleTypeInfo{}
	}
	spec := schema.Schema()
	if slices.Contains(spec.Type, "object") || spec.AllOf != nil || spec.OneOf != nil {
		return sampleTypeInfo{
			Package: parent.Package,
			Name:    parent.Name + strcase.ToCamel(property),
		}
	}
	return sampleTypeInfo{}
}

func (b *Builder) sampleArrayItemType(parent sampleTypeInfo, schema *base.SchemaProxy) sampleTypeInfo {
	if schema == nil {
		return sampleTypeInfo{}
	}
	if schema.GetReference() != "" {
		return sampleTypeInfo{
			Package: parent.Package,
			Name:    b.getReferenceSchema(schema),
		}
	}
	if schema.Schema() == nil {
		return sampleTypeInfo{}
	}
	spec := schema.Schema()
	if slices.Contains(spec.Type, "object") || spec.AllOf != nil || spec.OneOf != nil {
		name := parent.Name
		if before, ok := strings.CutSuffix(name, "Body"); ok {
			name = before
		}
		if before, ok := strings.CutSuffix(name, "Params"); ok {
			name = before
		}
		return sampleTypeInfo{
			Package: parent.Package,
			Name:    name + "Item",
		}
	}
	return sampleTypeInfo{}
}

func sampleStringExpr(schema *base.Schema, example any) (string, bool, error) {
	if example == nil {
		example = sampleDefaultString(schema)
	}

	value, _ := example.(string)
	switch schema.Format {
	case "date-time":
		return "datetime.datetime(2025, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)", true, nil
	case "date":
		return "datetime.date(2025, 1, 1)", true, nil
	case "time":
		return "datetime.time(12, 0, 0)", true, nil
	default:
		return strconv.Quote(value), false, nil
	}
}

func sampleIntegerExpr(example any) (string, bool, error) {
	switch v := example.(type) {
	case int:
		return strconv.Itoa(v), false, nil
	case int64:
		return strconv.FormatInt(v, 10), false, nil
	case float64:
		return strconv.FormatInt(int64(v), 10), false, nil
	default:
		return "1", false, nil
	}
}

func sampleNumberExpr(example any) (string, bool, error) {
	switch v := example.(type) {
	case float64:
		return strconv.FormatFloat(v, 'f', -1, 64), false, nil
	case float32:
		return strconv.FormatFloat(float64(v), 'f', -1, 32), false, nil
	case int:
		return strconv.Itoa(v), false, nil
	case int64:
		return strconv.FormatInt(v, 10), false, nil
	default:
		return "10.1", false, nil
	}
}

func sampleBoolExpr(example any) (string, bool, error) {
	if value, ok := example.(bool); ok {
		if value {
			return "True", false, nil
		}
		return "False", false, nil
	}
	return "True", false, nil
}

func sampleDefaultString(schema *base.Schema) string {
	switch schema.Format {
	case "uuid":
		return "00000000-0000-0000-0000-000000000000"
	case "uri", "url":
		return "https://example.com"
	case "email":
		return "user@example.com"
	case "date":
		return "2025-01-01"
	case "time":
		return "12:00:00"
	case "date-time":
		return "2025-01-01T12:00:00Z"
	case "password":
		return "secret"
	default:
		return "example"
	}
}

func renderCall(name string, args []string, level int) string {
	if len(args) == 0 {
		return name + "()"
	}

	var out strings.Builder
	out.WriteString(name)
	out.WriteString("(\n")
	for _, arg := range args {
		out.WriteString(indentPython(arg, level+1))
		out.WriteString(",\n")
	}
	out.WriteString(strings.Repeat("    ", level))
	out.WriteString(")")
	return out.String()
}

func renderListLiteral(items []string, level int) string {
	if len(items) == 0 {
		return "[]"
	}

	var out strings.Builder
	out.WriteString("[\n")
	for _, item := range items {
		out.WriteString(indentPython(item, level+1))
		out.WriteString(",\n")
	}
	out.WriteString(strings.Repeat("    ", level))
	out.WriteString("]")
	return out.String()
}

func renderDictLiteral(values map[string]any) string {
	keys := make([]string, 0, len(values))
	for key := range values {
		keys = append(keys, key)
	}
	sort.Strings(keys)

	parts := make([]string, 0, len(keys))
	for _, key := range keys {
		parts = append(parts, fmt.Sprintf("%q: %s", key, sampleAnyExpr(values[key])))
	}
	return "{" + strings.Join(parts, ", ") + "}"
}

func sampleAnyExpr(value any) string {
	switch v := value.(type) {
	case string:
		return strconv.Quote(v)
	case bool:
		if v {
			return "True"
		}
		return "False"
	case int:
		return strconv.Itoa(v)
	case int64:
		return strconv.FormatInt(v, 10)
	case float64:
		return strconv.FormatFloat(v, 'f', -1, 64)
	case []any:
		items := make([]string, 0, len(v))
		for _, item := range v {
			items = append(items, sampleAnyExpr(item))
		}
		return "[" + strings.Join(items, ", ") + "]"
	case map[string]any:
		return renderDictLiteral(v)
	default:
		return `"value"`
	}
}

func indentPython(s string, level int) string {
	prefix := strings.Repeat("    ", level)
	return prefix + strings.ReplaceAll(s, "\n", "\n"+prefix)
}

func requiredPropertySet(required []string) map[string]bool {
	set := make(map[string]bool, len(required))
	for _, name := range required {
		set[name] = true
	}
	return set
}

func orderedPropertyNames(properties *orderedmap.Map[string, *base.SchemaProxy]) []string {
	if properties == nil {
		return nil
	}
	names := make([]string, 0, properties.Len())
	for name := range properties.KeysFromOldest() {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

func sampleValueFromParameter(param *v3.Parameter) any {
	if param == nil {
		return nil
	}
	if value, ok := sampleValueFromYAMLNode(param.Example); ok {
		return value
	}
	if param.Examples != nil {
		for _, example := range param.Examples.FromOldest() {
			if example == nil {
				continue
			}
			if value, ok := sampleValueFromYAMLNode(example.Value); ok {
				return value
			}
		}
	}
	if param.Schema != nil {
		value, _ := sampleValueFromSchema(param.Schema.Schema())
		return value
	}
	return nil
}

func sampleValueFromMediaType(mt *v3.MediaType) any {
	if mt == nil {
		return nil
	}
	if value, ok := sampleValueFromYAMLNode(mt.Example); ok {
		return value
	}
	if mt.Examples != nil {
		for _, example := range mt.Examples.FromOldest() {
			if example == nil {
				continue
			}
			if value, ok := sampleValueFromYAMLNode(example.Value); ok {
				return value
			}
		}
	}
	if mt.Schema != nil && mt.Schema.Schema() != nil {
		value, _ := sampleValueFromSchema(mt.Schema.Schema())
		return value
	}
	return nil
}

func sampleValueFromSchema(schema *base.Schema) (any, bool) {
	if schema == nil {
		return nil, false
	}
	if value, ok := sampleValueFromYAMLNode(schema.Example); ok {
		return value, true
	}
	for _, example := range schema.Examples {
		if value, ok := sampleValueFromYAMLNode(example); ok {
			return value, true
		}
	}
	if value, ok := sampleValueFromYAMLNode(schema.Default); ok {
		return value, true
	}
	return nil, false
}

func sampleValueFromEnum(enum []*yaml.Node) any {
	for _, value := range enum {
		if decoded, ok := sampleValueFromYAMLNode(value); ok {
			return decoded
		}
	}
	return nil
}

func sampleValueFromYAMLNode(node *yaml.Node) (any, bool) {
	if node == nil {
		return nil, false
	}

	var value any
	if err := node.Decode(&value); err != nil {
		return nil, false
	}
	return value, true
}

func schemaProxyHasExplicitExample(schema *base.SchemaProxy) bool {
	if schema == nil || schema.Schema() == nil {
		return false
	}
	spec := schema.Schema()
	return spec.Example != nil || len(spec.Examples) > 0 || spec.Default != nil || spec.Const != nil || len(spec.Enum) > 0
}
