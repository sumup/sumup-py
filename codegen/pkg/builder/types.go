package builder

import (
	"fmt"
	"slices"
	"strings"
)

type Writable interface {
	String() string
}

type Type interface {
	TypeName() string
}

func indent(n int, s string) string {
	elems := strings.Split(s, "\n")
	for i := range elems {
		elems[i] = strings.Repeat("\t", n) + elems[i]
	}
	return strings.Join(elems, "\n")
}

func (c *ClassDeclaration) String() string {
	buf := new(strings.Builder)
	if c.RequestOnly {
		if c.AdditionalPropertiesType != "" {
			valueType := "typing.Any"
			if len(c.Fields) == 0 {
				valueType = inputTypeName(c.AdditionalPropertiesType)
			}
			fmt.Fprintf(buf, "%sInput = typing.Mapping[str, %s]\n", c.Name, valueType)
			if c.Description != "" {
				fmt.Fprintf(buf, "'''\n%s\n'''\n", c.Description)
			}
			return buf.String()
		}
		fmt.Fprintf(buf, "class %sInput(typing_extensions.TypedDict, total=False):\n", c.Name)
		if c.Description != "" {
			fmt.Fprintf(buf, "\t'''\n\t%s\n\t'''\n", c.Description)
		}
		if len(c.Fields) == 0 {
			fmt.Fprint(buf, "\tpass\n")
		} else {
			fields := append([]Property(nil), c.Fields...)
			slices.SortFunc(fields, func(a, b Property) int {
				if a.Optional && !b.Optional {
					return 1
				}
				if b.Optional && !a.Optional {
					return -1
				}
				return strings.Compare(a.Name, b.Name)
			})
			for _, ft := range fields {
				fmt.Fprint(buf, "\n")
				fmt.Fprint(buf, indent(1, ft.TypedDictFieldString()))
			}
		}
		fmt.Fprint(buf, "\n")
		return buf.String()
	}
	fmt.Fprintf(buf, "class %s(pydantic.BaseModel):\n", c.Name)
	if c.Description != "" {
		fmt.Fprintf(buf, "\t'''\n\t%s\n\t'''\n", c.Description)
	}
	if c.Fields != nil {
		slices.SortFunc(c.Fields, func(a, b Property) int {
			if a.Optional && !b.Optional {
				return 1
			}
			if b.Optional && !a.Optional {
				return -1
			}
			return strings.Compare(a.Name, b.Name)
		})
		for _, ft := range c.Fields {
			fmt.Fprint(buf, "\n")
			fmt.Fprint(buf, indent(1, ft.String()))
		}
	}
	if c.AdditionalPropertiesType != "" {
		fmt.Fprint(buf, "\n")
		fmt.Fprint(buf, "\tmodel_config = pydantic.ConfigDict(extra=\"allow\")\n")
		fmt.Fprint(buf, "\n")
		fmt.Fprint(buf, "\t@pydantic.model_validator(mode=\"before\")\n")
		fmt.Fprint(buf, "\t@classmethod\n")
		fmt.Fprint(buf, "\tdef _merge_additional_properties(cls, values: object) -> object:\n")
		fmt.Fprint(buf, "\t\tif not isinstance(values, dict):\n")
		fmt.Fprint(buf, "\t\t\treturn values\n")
		fmt.Fprint(buf, "\n")
		fmt.Fprint(buf, "\t\tvalues_dict = typing.cast(dict[str, object], values)\n")
		fmt.Fprint(buf, "\t\tadditional = values_dict.get(\"additional_properties\")\n")
		fmt.Fprint(buf, "\t\tif not isinstance(additional, dict):\n")
		fmt.Fprint(buf, "\t\t\treturn values\n")
		fmt.Fprint(buf, "\n")
		fmt.Fprint(buf, "\t\tmerged = dict(additional)\n")
		fmt.Fprint(buf, "\t\tfor key, value in values_dict.items():\n")
		fmt.Fprint(buf, "\t\t\tif key != \"additional_properties\":\n")
		fmt.Fprint(buf, "\t\t\t\tmerged[key] = value\n")
		fmt.Fprint(buf, "\n")
		fmt.Fprint(buf, "\t\treturn merged\n")
		fmt.Fprint(buf, "\n")
		fmt.Fprint(buf, "\t@property\n")
		fmt.Fprintf(buf, "\tdef additional_properties(self) -> dict[str, %s]:\n", c.AdditionalPropertiesType)
		fmt.Fprint(buf, "\t\tif self.model_extra is None:\n")
		fmt.Fprint(buf, "\t\t\tobject.__setattr__(self, \"__pydantic_extra__\", {})\n")
		fmt.Fprintf(buf, "\t\treturn typing.cast(dict[str, %s], self.model_extra)\n", c.AdditionalPropertiesType)
		fmt.Fprint(buf, "\n")
		fmt.Fprint(buf, "\t@additional_properties.setter\n")
		fmt.Fprintf(buf, "\tdef additional_properties(self, value: dict[str, %s]) -> None:\n", c.AdditionalPropertiesType)
		fmt.Fprint(buf, "\t\tobject.__setattr__(self, \"__pydantic_extra__\", dict(value))\n")
	}
	fmt.Fprint(buf, "\n")
	fmt.Fprintf(buf, "class %sDict(typing_extensions.TypedDict, total=False):\n", c.Name)
	if len(c.Fields) == 0 {
		fmt.Fprint(buf, "\tpass\n")
	} else {
		fields := append([]Property(nil), c.Fields...)
		slices.SortFunc(fields, func(a, b Property) int {
			if a.Optional && !b.Optional {
				return 1
			}
			if b.Optional && !a.Optional {
				return -1
			}
			return strings.Compare(a.Name, b.Name)
		})
		for _, ft := range fields {
			fmt.Fprint(buf, "\n")
			fmt.Fprint(buf, indent(1, ft.TypedDictFieldString()))
		}
	}
	fmt.Fprint(buf, "\n")
	fmt.Fprintf(buf, "%sInput = %sDict\n", c.Name, c.Name)
	fmt.Fprint(buf, "\n")
	return buf.String()
}

func (c *ClassDeclaration) TypeName() string {
	return c.Name
}

func (o *OneOfDeclaration) String() string {
	buf := new(strings.Builder)
	options := make([]string, 0, len(o.Options))
	for _, option := range o.Options {
		options = append(options, inputTypeName(option))
	}
	if o.RequestOnly {
		fmt.Fprintf(buf, "%sInput = typing.Union[%s]", o.Name, strings.Join(options, ", "))
		return buf.String()
	}
	fmt.Fprintf(buf, "%s = typing.Union[", o.Name)
	fmt.Fprint(buf, strings.Join(o.Options, ", "))
	fmt.Fprintf(buf, "]\n")
	fmt.Fprintf(buf, "%sInput = typing.Union[%s]", o.Name, strings.Join(options, ", "))
	return buf.String()
}

func (o *OneOfDeclaration) TypeName() string {
	return o.Name
}

func (p *Property) String() string {
	buf := new(strings.Builder)
	name := p.Name
	alias := p.SerializedName

	fieldName := pythonFieldName(name)

	useAlias := alias != "" && alias != fieldName

	if useAlias {
		aliasChoices := fmt.Sprintf("pydantic.AliasChoices(%q, %q)", alias, fieldName)
		if p.Optional {
			fmt.Fprintf(buf, "%s: typing.Optional[%s] = pydantic.Field(default=None, serialization_alias=%q, validation_alias=%s)\n", fieldName, p.Type, alias, aliasChoices)
		} else {
			fmt.Fprintf(buf, "%s: %s = pydantic.Field(serialization_alias=%q, validation_alias=%s)\n", fieldName, p.Type, alias, aliasChoices)
		}
	} else if p.Optional {
		fmt.Fprintf(buf, "%s: typing.Optional[%s] = None\n", fieldName, p.Type)
	} else {
		fmt.Fprintf(buf, "%s: %s\n", fieldName, p.Type)
	}
	if p.Comment != "" {
		fmt.Fprintf(buf, "'''\n%s\n'''\n", p.Comment)
	}

	return buf.String()
}

func (p Property) FieldName() string {
	return pythonFieldName(p.Name)
}

func (p Property) WireName() string {
	if p.SerializedName != "" {
		return p.SerializedName
	}
	return p.FieldName()
}

func (p Property) MethodParameterString() string {
	typeName := p.MethodParameterType()
	if p.Optional {
		return fmt.Sprintf("%s: typing.Union[%s, NotGivenType] = NOT_GIVEN", p.FieldName(), typeName)
	}

	return fmt.Sprintf("%s: %s", p.FieldName(), typeName)
}

func (p Property) MethodParameterType() string {
	return inputTypeName(p.Type)
}

func (p Property) BodyArgumentExpr() string {
	name := p.FieldName()
	if strings.HasPrefix(p.Type, "list[") {
		return fmt.Sprintf("list(%s)", name)
	}

	return name
}

func (p Property) TypedDictFieldString() string {
	typeName := inputTypeName(p.Type)
	if p.Comment != "" {
		typeName = fmt.Sprintf("typing_extensions.Annotated[%s, typing_extensions.Doc(%#v)]", typeName, p.Comment)
	}
	if p.Optional {
		return fmt.Sprintf("%s: typing_extensions.NotRequired[%s]", p.FieldName(), typeName)
	}

	return fmt.Sprintf("%s: typing_extensions.Required[%s]", p.FieldName(), typeName)
}

func (e *EnumDeclaration[E]) String() string {
	buf := new(strings.Builder)
	fmt.Fprintf(buf, "%s = typing.Union[typing.Literal[", e.Name)
	slices.Sort(e.Values)
	for i, v := range e.Values {
		if i != 0 {
			fmt.Fprint(buf, ", ")
		}
		fmt.Fprintf(buf, "%#v", v)
	}
	fmt.Fprintf(buf, "], %s]\n", pythonEnumBaseType(e.Type))
	fmt.Fprintf(buf, "%sInput = %s\n", e.Name, e.Name)
	return buf.String()
}

func (e *EnumDeclaration[E]) TypeName() string {
	return e.Name
}

func pythonFieldName(name string) string {
	if strings.HasPrefix(name, "+") {
		name = strings.Replace(name, "+", "Plus", 1)
	}
	if strings.HasPrefix(name, "-") {
		name = strings.Replace(name, "-", "Minus", 1)
	}
	if strings.HasPrefix(name, "@") {
		name = strings.Replace(name, "@", "At", 1)
	}
	if strings.HasPrefix(name, "$") {
		name = strings.Replace(name, "$", "", 1)
	}

	return name
}

func pythonEnumBaseType(typeName string) string {
	switch typeName {
	case "string":
		return "str"
	case "integer", "int", "int64":
		return "int"
	case "number", "float":
		return "float"
	default:
		return "typing.Any"
	}
}

func inputTypeName(typeName string) string {
	switch {
	case strings.HasPrefix(typeName, "list[") && strings.HasSuffix(typeName, "]"):
		return "typing.Sequence[" + inputTypeName(typeName[5:len(typeName)-1]) + "]"
	case strings.HasPrefix(typeName, "typing.Sequence[") && strings.HasSuffix(typeName, "]"):
		return "typing.Sequence[" + inputTypeName(typeName[len("typing.Sequence["):len(typeName)-1]) + "]"
	case strings.HasPrefix(typeName, "dict[") && strings.HasSuffix(typeName, "]"):
		args := splitTypeArgs(typeName[5 : len(typeName)-1])
		if len(args) == 2 {
			return fmt.Sprintf("typing.Mapping[%s, %s]", args[0], inputTypeName(args[1]))
		}
	case strings.HasPrefix(typeName, "typing.Mapping["),
		strings.HasPrefix(typeName, "typing.Literal["),
		strings.HasPrefix(typeName, "typing.Any"),
		strings.HasPrefix(typeName, "typing_extensions."):
		return typeName
	case strings.HasPrefix(typeName, "typing.Union[") && strings.HasSuffix(typeName, "]"):
		args := splitTypeArgs(typeName[len("typing.Union[") : len(typeName)-1])
		for i := range args {
			args[i] = inputTypeName(args[i])
		}
		return "typing.Union[" + strings.Join(args, ", ") + "]"
	case strings.HasPrefix(typeName, "typing.Optional[") && strings.HasSuffix(typeName, "]"):
		return "typing.Optional[" + inputTypeName(typeName[len("typing.Optional["):len(typeName)-1]) + "]"
	case isPrimitiveType(typeName):
		return typeName
	default:
		return typeName + "Input"
	}

	return typeName
}

func isPrimitiveType(typeName string) bool {
	switch typeName {
	case "str", "int", "float", "bool", "object", "datetime.date", "datetime.datetime", "datetime.time", "Secret":
		return true
	default:
		return false
	}
}

func splitTypeArgs(s string) []string {
	args := make([]string, 0, 2)
	start := 0
	depth := 0
	for i, r := range s {
		switch r {
		case '[':
			depth++
		case ']':
			depth--
		case ',':
			if depth == 0 {
				args = append(args, strings.TrimSpace(s[start:i]))
				start = i + 1
			}
		}
	}
	args = append(args, strings.TrimSpace(s[start:]))
	return args
}
