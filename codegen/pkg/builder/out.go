package builder

import (
	"bytes"
	"fmt"
	"log/slog"
	"os"
	"path"
	"path/filepath"
	"slices"
	"strings"

	"github.com/iancoleman/strcase"
	"github.com/pb33f/libopenapi/datamodel/high/base"
	v3 "github.com/pb33f/libopenapi/datamodel/high/v3"
)

type typesTemplateData struct {
	PackageName string
	Types       []Writable
	UsesSecret  bool
}

func (b *Builder) generateResourceTypes(tag *base.Tag, schemas []*base.SchemaProxy) error {
	types := b.schemasToTypes(schemas)
	usesSecret := usesSecretType(types)

	typesBuf := bytes.NewBuffer(nil)
	if err := b.templates.ExecuteTemplate(typesBuf, "types.py.tmpl", typesTemplateData{
		PackageName: strcase.ToSnake(tag.Name),
		Types:       types,
		UsesSecret:  usesSecret,
	}); err != nil {
		return err
	}

	dir := path.Join(b.cfg.Out, strcase.ToSnake(tag.Name))
	typeFileName := path.Join(dir, "types.py")
	typesFile, err := openGeneratedFile(typeFileName)
	if err != nil {
		return err
	}
	defer func() {
		_ = typesFile.Close()
	}()

	if _, err := typesFile.Write(typesBuf.Bytes()); err != nil {
		return err
	}

	return nil
}

type indexTemplateData struct {
	Service           string
	ResourceTypeNames []string
	TypeNames         []string
}

func (b *Builder) generateResourceIndex(tagName string, resourceTypes []string) error {
	tag := b.tagByTagName(tagName)

	resolvedSchemas := b.schemasByTag[tagName]
	typeNames := make([]string, 0, len(resolvedSchemas))
	for _, s := range resolvedSchemas {
		if name := b.getReferenceSchema(s); name != "" {
			typeNames = append(typeNames, name)
		}
	}
	slices.Sort(typeNames)

	typesBuf := bytes.NewBuffer(nil)
	if err := b.templates.ExecuteTemplate(typesBuf, "index.py.tmpl", indexTemplateData{
		TypeNames:         typeNames,
		ResourceTypeNames: resourceTypes,
		Service:           strcase.ToCamel(tag.Name),
	}); err != nil {
		return err
	}

	dir := path.Join(b.cfg.Out, strcase.ToSnake(tag.Name))
	typeFileName := path.Join(dir, "__init__.py")
	typesFile, err := openGeneratedFile(typeFileName)
	if err != nil {
		return err
	}
	defer func() {
		_ = typesFile.Close()
	}()

	if _, err := typesFile.Write(typesBuf.Bytes()); err != nil {
		return err
	}

	return nil
}

type resourceTemplateData struct {
	PackageName string
	TypeNames   []string
	Params      []Writable
	Service     string
	Methods     []*Method
	UsesSecret  bool
}

func (b *Builder) generateResourceFile(tagName string, paths *v3.Paths) ([]string, error) {
	tag := b.tagByTagName(tagName)

	resolvedSchemas := b.schemasByTag[tagName]
	if err := b.generateResourceTypes(tag, b.schemasByTag[tagName]); err != nil {
		return nil, err
	}

	typeNames := make([]string, 0, len(resolvedSchemas))
	for _, s := range resolvedSchemas {
		if name := b.getReferenceSchema(s); name != "" {
			typeNames = append(typeNames, name)
		}
	}
	slices.Sort(typeNames)

	bodyTypes := b.pathsToBodyTypes(paths)
	innerTypes := bodyTypes

	paramTypes := b.pathsToParamTypes(paths)
	innerTypes = append(innerTypes, paramTypes...)

	responseTypes := b.pathsToResponseTypes(paths)
	innerTypes = append(innerTypes, responseTypes...)

	methods, err := b.pathsToMethods(paths)
	if err != nil {
		return nil, fmt.Errorf("convert paths to methods: %w", err)
	}

	slog.Info("generating file",
		slog.String("tag", tag.Name),
		slog.Int("schema_structs", len(typeNames)),
		slog.Int("body_structs", len(bodyTypes)),
		slog.Int("path_params_structs", len(paramTypes)),
		slog.Int("methods", len(methods)),
	)

	usesSecret := usesSecretType(innerTypes)

	serviceBuf := bytes.NewBuffer(nil)
	if err := b.templates.ExecuteTemplate(serviceBuf, "resource.py.tmpl", resourceTemplateData{
		PackageName: strcase.ToSnake(tag.Name),
		TypeNames:   typeNames,
		Params:      innerTypes,
		Service:     strcase.ToCamel(tag.Name),
		Methods:     methods,
		UsesSecret:  usesSecret,
	}); err != nil {
		return nil, err
	}

	dir := path.Join(b.cfg.Out, strcase.ToSnake(tag.Name))
	resourceFileName := path.Join(dir, "resource.py")
	resourceFile, err := openGeneratedFile(resourceFileName)
	if err != nil {
		return nil, err
	}
	defer func() {
		_ = resourceFile.Close()
	}()

	if _, err := resourceFile.Write(serviceBuf.Bytes()); err != nil {
		return nil, err
	}

	resourceTypes := make([]string, 0, len(innerTypes))
	for _, t := range innerTypes {
		if typ, ok := t.(Type); ok {
			resourceTypes = append(resourceTypes, typ.TypeName())
		}
	}

	return resourceTypes, nil
}

func (b *Builder) generateResource(tagName string, paths *v3.Paths) error {
	if tagName == "" {
		return fmt.Errorf("empty tag name")
	}

	tag := b.tagByTagName(tagName)

	dir := path.Join(b.cfg.Out, strcase.ToSnake(tag.Name))
	if err := os.MkdirAll(dir, os.ModePerm); err != nil {
		return err
	}

	if err := b.generateResourceTypes(tag, b.schemasByTag[tagName]); err != nil {
		return err
	}

	resourceTypes, err := b.generateResourceFile(tagName, paths)
	if err != nil {
		return err
	}

	if err := b.generateResourceIndex(tagName, resourceTypes); err != nil {
		return err
	}

	return nil
}

func usesSecretType(writables []Writable) bool {
	for _, w := range writables {
		if writableUsesSecret(w) {
			return true
		}
	}
	return false
}

func writableUsesSecret(w Writable) bool {
	switch typed := w.(type) {
	case *ClassDeclaration:
		for _, f := range typed.Fields {
			if strings.Contains(f.Type, "Secret") {
				return true
			}
		}
	case *TypeAlias:
		if strings.Contains(typed.Type, "Secret") {
			return true
		}
	}
	return false
}

func (b *Builder) writeClientFile(fname string, tags []string) error {
	f, err := os.OpenFile(fname, os.O_RDWR|os.O_CREATE|os.O_TRUNC, os.FileMode(0o755))
	if err != nil {
		return fmt.Errorf("create %q: %w", fname, err)
	}
	defer func() {
		_ = f.Close()
	}()

	type resource struct {
		Name    string
		Package string
	}

	resources := make([]resource, 0, len(tags))
	for i := range tags {
		if p := b.pathsByTag[tags[i]]; p.PathItems.Len() == 0 {
			continue
		}
		resources = append(resources, resource{
			Name:    strcase.ToCamel(tags[i]),
			Package: strcase.ToSnake(tags[i]),
		})
	}

	slices.SortFunc(resources, func(a, b resource) int {
		return strings.Compare(a.Name, b.Name)
	})

	if err := b.templates.ExecuteTemplate(f, "client.py.tmpl", map[string]any{
		"Version":   b.spec.Info.Version,
		"Resources": resources,
	}); err != nil {
		return fmt.Errorf("generate client: %w", err)
	}

	return nil
}

func (b *Builder) writeAPIVersionFile(fname string) error {
	f, err := os.OpenFile(fname, os.O_RDWR|os.O_CREATE|os.O_TRUNC, os.FileMode(0o755))
	if err != nil {
		return fmt.Errorf("create %q: %w", fname, err)
	}
	defer func() {
		_ = f.Close()
	}()

	if err := b.templates.ExecuteTemplate(f, "api_version.py.tmpl", map[string]any{
		"Version": b.spec.Info.Version,
	}); err != nil {
		return fmt.Errorf("generate api version: %w", err)
	}

	return nil
}

func openGeneratedFile(filename string) (*os.File, error) {
	cwd, err := os.Getwd()
	if err != nil {
		return nil, fmt.Errorf("get current working directory: %w", err)
	}

	p := filepath.Join(cwd, filename)
	f, err := os.OpenFile(p, os.O_RDWR|os.O_CREATE|os.O_TRUNC, os.FileMode(0o755))
	if err != nil {
		return nil, fmt.Errorf("create %q: %w", p, err)
	}

	return f, nil
}

func (b *Builder) tagByTagName(name string) *base.Tag {
	idx := slices.IndexFunc(b.spec.Tags, func(tag *base.Tag) bool {
		return strings.EqualFold(tag.Name, name)
	})
	tag := &base.Tag{
		Name: name,
	}
	if idx != -1 {
		tag = b.spec.Tags[idx]
	}
	return tag
}
