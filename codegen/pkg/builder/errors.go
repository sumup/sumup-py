package builder

import (
	"fmt"
	"strings"

	v3 "github.com/pb33f/libopenapi/datamodel/high/v3"
)

type errorResponseFormat struct {
	ContentType string
	Type        string
	content     *v3.MediaType
}

func (b *Builder) errorResponseFormats(operationName string, response *v3.Response, code string) []errorResponseFormat {
	var formats []errorResponseFormat
	for contentType, content := range response.Content.FromOldest() {
		if contentType != "application/json" && contentType != "application/problem+json" {
			continue
		}
		if content == nil || content.Schema == nil || content.Schema.Schema() == nil {
			continue
		}
		formats = append(formats, errorResponseFormat{ContentType: contentType, content: content})
	}
	for i := range formats {
		format := &formats[i]
		if format.content.Schema.IsReference() {
			format.Type = b.getReferenceSchema(format.content.Schema)
			continue
		}
		name := operationName
		if len(formats) > 1 {
			if format.ContentType == "application/problem+json" {
				name += "Problem"
			} else {
				name += "Json"
			}
		}
		format.Type = b.getResponseName(name, code, format.content)
	}
	return formats
}

func errorRaise(message, bodyType string) string {
	argument := ""
	if bodyType != "" {
		argument = ", body_type=" + bodyType
	}
	return fmt.Sprintf("raise APIError.from_response(%q, resp%s)", message, argument)
}

func (response Response) ErrorStatement() string {
	if len(response.Formats) == 0 {
		return errorRaise(response.ErrDescription, response.Type)
	}
	var output strings.Builder
	output.WriteString("content_type = resp.headers.get(\"Content-Type\", \"\").split(\";\", 1)[0].strip().lower()\n")
	for i, format := range response.Formats {
		condition := "elif"
		if i == 0 {
			condition = "if"
		}
		fmt.Fprintf(&output, "%s content_type == %q:\n\t%s\n", condition, format.ContentType,
			errorRaise(response.ErrDescription, format.Type))
	}
	fmt.Fprintf(&output, "else:\n\t%s", errorRaise(response.ErrDescription, ""))
	return output.String()
}

func (response Response) ErrorType() string {
	switch response.Code {
	case 400:
		return "BadRequestError"
	case 401:
		return "AuthenticationError"
	case 403:
		return "PermissionDeniedError"
	case 404:
		return "NotFoundError"
	case 409:
		return "ConflictError"
	case 422:
		return "UnprocessableEntityError"
	case 429:
		return "RateLimitError"
	}
	if response.Code >= 500 && response.Code < 600 {
		return "InternalServerError"
	}
	if response.Code >= 400 && response.Code < 500 {
		return "APIStatusError"
	}
	return "APIError"
}
