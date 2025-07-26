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

	if p.Optional {
		fmt.Fprintf(buf, "%s: typing.Optional[%s] = None\n", name, p.Type)
	} else {
		fmt.Fprintf(buf, "%s: %s\n", name, p.Type)
	}
	if p.Comment != "" {
		fmt.Fprintf(buf, "'''\n%s\n'''\n", p.Comment)
	}

	return buf.String()
}

func (e *EnumDeclaration[E]) String() string {
	buf := new(strings.Builder)
	fmt.Fprintf(buf, "%s = typing.Literal[", e.Name)
	slices.Sort(e.Values)
	for i, v := range e.Values {
		if i != 0 {
			fmt.Fprint(buf, ", ")
		}
		fmt.Fprintf(buf, "%#v", v)
	}
	fmt.Fprint(buf, "]\n")
	return buf.String()
}

func (e *EnumDeclaration[E]) TypeName() string {
	return e.Name
}
