package builder

import (
	"fmt"
	"slices"
	"strings"
	"unicode"
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
	fmt.Fprint(buf, "\n")
	return buf.String()
}

func (c *ClassDeclaration) TypeName() string {
	return c.Name
}

func (o *OneOfDeclaration) String() string {
	buf := new(strings.Builder)
	fmt.Fprintf(buf, "%s = typing.Union[", o.Name)
	fmt.Fprint(buf, strings.Join(o.Options, ", "))
	fmt.Fprintf(buf, "]")
	return buf.String()
}

func (o *OneOfDeclaration) TypeName() string {
	return o.Name
}

func (p *Property) String() string {
	buf := new(strings.Builder)
	name := p.Name
	alias := p.SerializedName

	// TODO: extract into helper
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

	fieldName := name

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

func (e *EnumDeclaration[E]) String() string {
	buf := new(strings.Builder)
	fmt.Fprintf(buf, "class %s(%s):\n", e.Name, e.pythonBaseType())
	if e.Comment != "" {
		fmt.Fprintf(buf, "\t'''\n\t%s\n\t'''\n", e.Comment)
	}

	slices.Sort(e.Values)
	if len(e.Values) == 0 {
		fmt.Fprint(buf, "\tpass\n\n")
		return buf.String()
	}

	usedNames := map[string]int{}
	for i, v := range e.Values {
		if i == 0 && e.Comment != "" {
			fmt.Fprint(buf, "\n")
		}
		valueName := uniqueEnumFieldName(enumFieldName(fmt.Sprint(v)), usedNames)
		fmt.Fprintf(buf, "\t%s: %q = typing.cast(%q, %#v)\n", valueName, e.Name, e.Name, v)
	}
	fmt.Fprint(buf, "\n")
	return buf.String()
}

func (e *EnumDeclaration[E]) TypeName() string {
	return e.Name
}

func (e *EnumDeclaration[E]) pythonBaseType() string {
	switch e.Type {
	case "string":
		return "_OpenStrEnum"
	case "int", "int64":
		return "_OpenIntEnum"
	case "float":
		return "_OpenFloatEnum"
	default:
		return "_OpenStrEnum"
	}
}

func enumFieldName(raw string) string {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		raw = "VALUE"
	}

	var b strings.Builder
	lastUnderscore := false
	for _, r := range raw {
		switch {
		case unicode.IsLetter(r):
			b.WriteRune(unicode.ToUpper(r))
			lastUnderscore = false
		case unicode.IsDigit(r):
			b.WriteRune(r)
			lastUnderscore = false
		default:
			if !lastUnderscore && b.Len() > 0 {
				b.WriteRune('_')
				lastUnderscore = true
			}
		}
	}

	name := strings.Trim(b.String(), "_")
	if name == "" {
		name = "VALUE"
	}
	if unicode.IsDigit(rune(name[0])) {
		name = "VALUE_" + name
	}

	return name
}

func uniqueEnumFieldName(base string, used map[string]int) string {
	if base == "" {
		base = "VALUE"
	}
	if count, ok := used[base]; ok {
		count++
		used[base] = count
		return fmt.Sprintf("%s_%d", base, count)
	}
	used[base] = 1
	return base
}
