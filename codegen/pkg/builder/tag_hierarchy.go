package builder

import (
	"cmp"
	"fmt"
	"slices"
	"strings"

	"github.com/iancoleman/strcase"

	v3 "github.com/pb33f/libopenapi/datamodel/high/v3"
)

type resourceParent struct {
	tag   string
	label string
}

func readResourceParents(doc *v3.Document) (map[string]resourceParent, error) {
	if doc.Extensions == nil {
		return nil, nil
	}
	node, ok := doc.Extensions.Get("x-tagGroups")
	if !ok {
		return nil, nil
	}
	var groups []struct {
		Name string   `yaml:"name"`
		Tags []string `yaml:"tags"`
	}
	if err := node.Decode(&groups); err != nil {
		return nil, fmt.Errorf("decode x-tagGroups: %w", err)
	}
	labels := make(map[string]string, len(doc.Tags))
	for _, tag := range doc.Tags {
		var displayName string
		if tag.Extensions != nil {
			if label, ok := tag.Extensions.Get("x-displayName"); ok {
				if err := label.Decode(&displayName); err != nil {
					return nil, fmt.Errorf("decode x-displayName for %s: %w", tag.Name, err)
				}
			}
		}
		labels[tag.Name] = cmp.Or(displayName, tag.Name)
	}
	parents := map[string]resourceParent{}
	for _, group := range groups {
		if labels[group.Name] == "" {
			continue
		}
		for _, child := range group.Tags {
			if child == group.Name || labels[child] == "" || parents[child].tag != "" {
				continue
			}
			for ancestor := group.Name; ancestor != ""; ancestor = parents[ancestor].tag {
				if ancestor == child {
					return nil, fmt.Errorf("tag hierarchy contains a cycle at %s", child)
				}
			}
			parents[child] = resourceParent{tag: group.Name, label: labels[child]}
		}
	}
	return parents, nil
}

func (b *Builder) pathForResource(path *v3.PathItem, tag string) *v3.PathItem {
	operation := func(op *v3.Operation) *v3.Operation {
		if op == nil {
			return nil
		}
		owner := "shared"
		if len(op.Tags) > 0 {
			owner = strings.ToLower(op.Tags[0])
		}
		for ; owner != ""; owner = b.resourceParents[owner].tag {
			if owner == tag {
				copy := *op
				copy.Parameters = slices.Clone(op.Parameters)
				return &copy
			}
		}
		return nil
	}
	return &v3.PathItem{
		Parameters: path.Parameters,
		Get:        operation(path.Get), Put: operation(path.Put), Post: operation(path.Post),
		Delete: operation(path.Delete), Options: operation(path.Options), Head: operation(path.Head),
		Patch: operation(path.Patch), Trace: operation(path.Trace),
	}
}

type childResource struct {
	Name    string
	Service string
	Package string
}

func (b *Builder) children(tag string) []childResource {
	var children []childResource
	for child, parent := range b.resourceParents {
		if parent.tag == tag && b.pathsByTag[child] != nil {
			name := b.tagByTagName(child).Name
			children = append(children, childResource{Name: strcase.ToSnake(parent.label), Service: strcase.ToCamel(name), Package: strcase.ToSnake(name)})
		}
	}
	slices.SortFunc(children, func(a, b childResource) int { return cmp.Compare(a.Name, b.Name) })
	return children
}

func (b *Builder) resourcePath(tag string) string {
	if parent := b.resourceParents[tag]; parent.tag != "" {
		return b.resourcePath(parent.tag) + "." + strcase.ToSnake(parent.label)
	}
	return strcase.ToSnake(tag)
}

// scopedMethodNames removes a resource suffix when the shorter name is unambiguous.
func scopedMethodNames(names []string, suffixes ...string) map[string]string {
	original := make(map[string]bool, len(names))
	proposed := make(map[string]string, len(names))
	counts := make(map[string]int, len(names))
	for _, name := range names {
		original[name] = true
		short := unqualifiedMethodName(name, suffixes)
		proposed[name] = short
		counts[short]++
	}
	for name, short := range proposed {
		if original[short] || counts[short] > 1 {
			delete(proposed, name)
		}
	}
	return proposed
}

func unqualifiedMethodName(name string, suffixes []string) string {
	for _, suffix := range suffixes {
		for _, ending := range []string{suffix, strings.TrimSuffix(suffix, "s")} {
			if ending != "" {
				if short, found := strings.CutSuffix(name, ending); found && short != "" {
					return short
				}
			}
		}
	}
	return name
}

func (b *Builder) nestedMethodName(tag, original string) string {
	parent := b.resourceParents[tag]
	paths := b.pathsByTag[tag]
	if parent.tag == "" || paths == nil {
		return original
	}
	var names []string
	for path := range paths.PathItems.ValuesFromOldest() {
		for op := range path.GetOperations().ValuesFromOldest() {
			names = append(names, operationMethodName(op))
		}
	}
	scoped := scopedMethodNames(names, "_"+strcase.ToSnake(b.tagByTagName(tag).Name), "_"+strcase.ToSnake(parent.label))
	return cmp.Or(scoped[original], original)
}
