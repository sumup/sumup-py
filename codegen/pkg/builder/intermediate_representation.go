package builder

import (
	"cmp"
	"fmt"
	"strings"
)

// ClassDeclaration holds the information for generating a type.
// TODO: split into struct, alias, etc.
type ClassDeclaration struct {
	// Name of the type
	Name string
	// Type describes the type of the type (e.g. struct, int64, string)
	Type string
	// Fields holds the information for the field
	Fields []Property
	// Description holds the description of the type
	Description string
	// AdditionalPropertiesType holds the value type for additional properties if enabled.
	AdditionalPropertiesType string
	// RequestOnly marks request-only helper types that should not emit response models.
	RequestOnly bool
}

type OneOfDeclaration struct {
	Name        string
	Options     []string
	RequestOnly bool
}

// Property holds the information for Property of a type.
type Property struct {
	// Name of the field
	Name string
	// SerializedName is the original identifier used when encoding (e.g. query parameter name).
	SerializedName string
	// Type of the field, either primitive type (e.g. string) or if the field
	// is a schema reference then the type of the schema.
	Type string
	// Optional field.
	Optional bool

	Comment string
}

// EnumDeclaration holds the information for enum types
type EnumDeclaration[E cmp.Ordered] struct {
	// Name of the type
	Name string
	// Type describes the type of the type (e.g. struct, int64, string)
	Type string
	// Comment holds the description of the type
	Comment string
	Values  []E
}

type Response struct {
	IsErr          bool
	IsDefault      bool
	IsUnexpected   bool
	Type           string
	Code           int
	ErrDescription string
}

type TypeAlias struct {
	// Name of the type
	Name string
	// Type describes the type of the type (e.g. struct, int64, string)
	Type string
	// Comment holds the description of the type
	Comment string
	// RequestOnly marks request-only helper types that should only emit input aliases.
	RequestOnly bool
}

func (ta *TypeAlias) String() string {
	buf := new(strings.Builder)
	if ta.RequestOnly {
		fmt.Fprintf(buf, "%sInput = %s\n", ta.Name, inputTypeName(ta.Type))
		if ta.Comment != "" {
			fmt.Fprintf(buf, "'''\n%s\n'''\n", ta.Comment)
		}
		return buf.String()
	}
	fmt.Fprintf(buf, "%s = %s\n", ta.Name, ta.Type)
	fmt.Fprintf(buf, "%sInput = %s\n", ta.Name, inputTypeName(ta.Type))
	if ta.Comment != "" {
		fmt.Fprintf(buf, "'''\n%s\n'''\n", ta.Comment)
	}
	return buf.String()
}
