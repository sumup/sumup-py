package builder

import (
	"errors"
	"fmt"
	"log/slog"
	"regexp"
	"slices"
	"strconv"
	"strings"

	"github.com/iancoleman/strcase"
	"github.com/pb33f/libopenapi/datamodel/high/base"
	v3 "github.com/pb33f/libopenapi/datamodel/high/v3"

	"github.com/sumup/sumup-py/codegen/internal/stringx"
	"github.com/sumup/sumup-py/codegen/pkg/extension"
)

var (
	pathParamRegexp = regexp.MustCompile(`\{(\w+)\}`)
)

// Parameter is a method parameter.
type Parameter struct {
	Name string
	Type string
}

// Method describes a client method. Methods map one-to-one to OpenAPI operations.
type Method struct {
	Description       string
	DeprecationNotice *string
	Method            string
	FunctionName      string
	ResponseType      *string
	Path              string
	PathParams        []Parameter
	QueryParams       *Parameter
	HasBody           bool
	Responses         []Response
}

func (mt Method) ParamsString() string {
	res := strings.Builder{}
	res.WriteString("self")
	for _, p := range mt.PathParams {
		res.WriteString(", ")
		res.WriteString(fmt.Sprintf("%s: %s", strcase.ToSnake(p.Name), p.Type))
	}
	if mt.QueryParams != nil {
		res.WriteString(", ")
		res.WriteString(fmt.Sprintf("%s: typing.Optional[%s] = None", strcase.ToSnake(mt.QueryParams.Name), mt.QueryParams.Type))
	}
	return res.String()
}

// pathsToMethods converts openapi3 path to golang methods.
func (b *Builder) pathsToMethods(paths *v3.Paths) ([]*Method, error) {
	allMethods := make([]*Method, 0, paths.PathItems.Len())

	for path, pathItem := range paths.PathItems.FromOldest() {
		methods, err := b.pathToMethods(path, pathItem)
		if err != nil {
			return nil, err
		}

		allMethods = append(allMethods, methods...)
	}

	return allMethods, nil
}

// pathToMethods converts single openapi3 path to golang methods.
func (b *Builder) pathToMethods(path string, p *v3.PathItem) ([]*Method, error) {
	methods := make([]*Method, 0, p.GetOperations().Len())
	for method, operationSpec := range p.GetOperations().FromOldest() {
		operationSpec.Parameters = append(operationSpec.Parameters, p.Parameters...)
		method, err := b.operationToMethod(method, path, operationSpec)
		if err != nil {
			return nil, err
		}

		methods = append(methods, method)
	}

	return methods, nil
}

func pathBuilder(path string) string {
	var res strings.Builder

	res.WriteString(`f"`)
	for i, part := range strings.Split(path, "/") {
		if i != 0 {
			res.WriteString("/")
		}
		match := pathParamRegexp.FindStringSubmatch(part)
		if match == nil {
			res.WriteString(part)
		} else {
			res.WriteString(fmt.Sprintf("{%s}", strcase.ToSnake(match[1])))
		}
	}
	res.WriteString(`"`)

	return res.String()
}

func (b *Builder) operationToMethod(method, path string, o *v3.Operation) (*Method, error) {
	respType, err := b.getSuccessResponseType(o)
	if err != nil {
		return nil, fmt.Errorf("get successful response type: %w", err)
	}

	methodName := strcase.ToSnake(o.OperationId)
	if ext, ok := extension.Get[map[string]any](o.Extensions, "x-codegen"); ok {
		//nolint:errcheck // FIXME: type assertion
		if name, ok := ext["method_name"]; ok {
			//nolint:errcheck // FIXME: type assertion
			methodName = strcase.ToSnake(name.(string))
		}
	}

	params, err := b.buildPathParams("path", o.Parameters)
	if err != nil {
		return nil, fmt.Errorf("build path parameters: %w", err)
	}

	if o.RequestBody != nil {
		mt, ok := o.RequestBody.Content.Get("application/json")
		if ok && mt.Schema != nil {
			params = append(params, Parameter{
				Name: "body",
				Type: strcase.ToCamel(o.OperationId) + "Body",
			})
		}
	}

	var queryParams *Parameter
	if slices.ContainsFunc(o.Parameters, func(p *v3.Parameter) bool {
		return p.In != "path" && p.In != "header"
	}) {
		queryParams = &Parameter{
			Name: "params",
			Type: strcase.ToCamel(o.OperationId) + "Params",
		}
	}

	responses := make([]Response, 0, o.Responses.Codes.Len())
	for code, resp := range o.Responses.Codes.FromOldest() {
		operationName := strcase.ToCamel(o.OperationId)
		typ := b.responseToType(operationName, resp, code)

		description := code
		if resp.Description != "" {
			description = resp.Description
		}

		statusCode, _ := strconv.Atoi(strings.ReplaceAll(code, "XX", "00"))
		responses = append(responses, Response{
			IsErr:          !strings.HasPrefix(code, "2"),
			IsDefault:      code == "default",
			Type:           typ,
			Code:           statusCode,
			ErrDescription: strings.TrimSpace(description),
		})
	}

	slices.SortFunc(responses, func(a, b Response) int {
		if a.IsDefault {
			return 1000
		}

		if b.IsDefault {
			return -1000
		}

		return a.Code - b.Code
	})

	slog.Info("generating method",
		slog.String("id", o.OperationId),
		slog.String("method_name", methodName),
	)

	return &Method{
		Description:       methodDoc(o),
		DeprecationNotice: deprecationNotice(o),
		Method:            strings.ToLower(method),
		FunctionName:      methodName,
		ResponseType:      respType,
		Path:              pathBuilder(path),
		PathParams:        params,
		QueryParams:       queryParams,
		HasBody:           o.RequestBody != nil,
		Responses:         responses,
	}, nil
}

func (b *Builder) getSuccessResponseType(o *v3.Operation) (*string, error) {
	type responseInfo struct {
		content *v3.MediaType
		code    string
	}

	sucessResponses := make([]responseInfo, 0)
	for name, response := range o.Responses.Codes.FromOldest() {
		// TODO: throw error here?
		if name == "default" {
			name = "400"
		}

		statusCode, err := strconv.Atoi(strings.ReplaceAll(name, "XX", "00"))
		if err != nil {
			return nil, fmt.Errorf("error converting %q to an integer: %w", name, err)
		}

		if statusCode < 200 || statusCode >= 300 {
			// Continue early, we just want the successful response.
			continue
		}

		if response.Content == nil {
			continue
		}

		if content, ok := response.Content.Get("application/json"); ok {
			sucessResponses = append(sucessResponses, responseInfo{
				content: content,
				code:    name,
			})
		}
	}

	if len(sucessResponses) == 0 {
		return nil, nil
	}

	if len(sucessResponses) == 1 {
		resp := sucessResponses[0]
		if resp.content.Schema.IsReference() {
			typ := b.getReferenceSchema(resp.content.Schema)
			return &typ, nil
		}

		operationName := strcase.ToCamel(o.OperationId)
		typ := b.getResponseName(operationName, resp.code, resp.content)
		return &typ, nil
	}

	operationName := strcase.ToCamel(o.OperationId)
	typ := operationName + "Response"
	return &typ, nil
}

func (b *Builder) responseToType(operationName string, resp *v3.Response, code string) string {
	if resp.GoLow().IsReference() {
		return strcase.ToCamel(strings.TrimPrefix(resp.GoLow().GetReference(), "#/components/responses/")) + "Response"
	}

	if resp.Content == nil {
		return ""
	}

	content, ok := resp.Content.Get("application/json")
	if !ok {
		return ""
	}

	if content.Schema.IsReference() {
		return b.getReferenceSchema(content.Schema)
	}

	return b.getResponseName(operationName, code, content)
}

func (b *Builder) buildPathParams(paramType string, params []*v3.Parameter) ([]Parameter, error) {
	if len(params) == 0 {
		return nil, nil
	}

	pathParams := make([]Parameter, 0)
	if paramType != "query" && paramType != "path" {
		return nil, errors.New("paramType must be one of 'query' or 'path'")
	}

	for _, p := range params {
		if p.In != "path" {
			continue
		}

		pathParams = append(pathParams, Parameter{
			Name: p.Name,
			Type: b.convertToValidPyType(p.Name, p.Schema),
		})
	}

	return pathParams, nil
}

// convertToValidPyType converts a schema type to a valid Go type.
func (b *Builder) convertToValidPyType(property string, r *base.SchemaProxy) string {
	// Use reference as it is the type
	if r.IsReference() {
		return b.getReferenceSchema(r)
	}

	schema := r.Schema()

	if schema.AdditionalProperties != nil && schema.AdditionalProperties.IsA() {
		if schema.AdditionalProperties.A.IsReference() {
			return b.getReferenceSchema(schema.AdditionalProperties.A)
		} else if schema.AdditionalProperties.A.Schema().Items.A.IsReference() {
			return b.getReferenceSchema(schema.AdditionalProperties.A.Schema().Items.A)
		}
		// TODO: what here?
	}

	// TODO: Handle AllOf
	if schema.AllOf != nil {
		if len(schema.AllOf) > 1 {
			slog.Warn(fmt.Sprintf("TODO: allOf for %q has more than 1 item\n", property))
			return "TODO"
		}

		return b.convertToValidPyType(property, schema.AllOf[0])
	}

	switch {
	case slices.Contains(schema.Type, "string"):
		return formatStringType(schema)
	case slices.Contains(schema.Type, "integer"):
		return "int"
	case slices.Contains(schema.Type, "number"):
		return "float"
	case slices.Contains(schema.Type, "boolean"):
		return "bool"
	case slices.Contains(schema.Type, "array"):
		reference := b.getReferenceSchema(schema.Items.A)
		if reference != "" {
			return fmt.Sprintf("[]%s", reference)
		}
		// TODO: handle if it is not a reference.
		return "list[str]"
	case slices.Contains(schema.Type, "object"):
		if schema.Properties.Len() == 0 {
			// TODO: generate type alias?
			slog.Warn("object with empty properties", slog.String("property", property))
			return "typing.Any"
		}
		// Most likely this is a local object, we will handle it.
		// TODO:
		return strcase.ToCamel(property)
	default:
		slog.Warn("unknown type, falling back to 'typing.Any'",
			slog.Any("property", property),
			slog.Any("type", schema.Type),
		)
		return "typing.Any"
	}
}

func (b *Builder) getReferenceSchema(v *base.SchemaProxy) string {
	if v.GoLow().IsReference() {
		ref := strings.TrimPrefix(v.GetReference(), "#/components/schemas/")
		if len(v.Schema().Enum) > 0 {
			return strcase.ToCamel(stringx.MakeSingular(ref))
		}

		return strcase.ToCamel(ref)
	}

	return ""
}

// formatStringType converts a string schema to a valid Go type.
func formatStringType(t *base.Schema) string {
	switch t.Format {
	case "date-time":
		return "datetime.datetime"
	case "date":
		return "datetime.date"
	case "time":
		return "datetime.time"
	default:
		return "str"
	}
}
