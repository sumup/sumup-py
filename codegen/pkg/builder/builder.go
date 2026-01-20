package builder

import (
	"fmt"
	"log/slog"
	"maps"
	"path"
	"slices"
	"strings"
	"text/template"
	"time"

	"github.com/pb33f/libopenapi/datamodel/high/base"
	v3 "github.com/pb33f/libopenapi/datamodel/high/v3"

	"github.com/sumup/sumup-py/codegen/templates"
)

// Builder is an SDK builder. Builder works in two steps:
// First, it loads the OpenAPI specs and pre-processes them for code generation
// by transforming the specs into intermediary representation.
// Secondly, it generates and writes the SDK to desired destination.
type Builder struct {
	cfg Config

	// spec are the OpenAPI specs we are working with.
	// Load the specs using [Builder.Load].
	spec *v3.Document

	// schemasByTag maps tags to respective schema references.
	schemasByTag map[string][]*base.SchemaProxy

	pathsByTag map[string]*v3.Paths

	templates *template.Template

	start time.Time
}

// Config is builder configuration which configures output options.
type Config struct {
	// Out is the output directory that the SDK will be written to.
	Out string
}

type Option func(b *Builder)

// New creates a new [Builder]. Call [Build.Load] to load in OpenAPI specs and
// [Build.Build] to generate SDK based on provided config.
func New(cfg Config, opts ...Option) *Builder {
	templates, err := template.New("").Funcs(template.FuncMap{
		"httpStatusCode": httpStatusCode,
		"indent":         indent,
		"join":           join,
	}).ParseFS(templates.Templates, "*")
	if err != nil {
		panic(err)
	}

	b := &Builder{
		cfg:          cfg,
		schemasByTag: make(map[string][]*base.SchemaProxy),
		pathsByTag:   make(map[string]*v3.Paths),
		templates:    templates,
	}

	for _, o := range opts {
		o(b)
	}

	return b
}

// Load loads OpenAPI specs into the builder.
// To generated the SDK, call [Builder.Build].
func (b *Builder) Load(spec *v3.Document) error {
	b.start = time.Now()
	b.spec = spec

	b.collectPaths()
	b.collectSchemas()

	return nil
}

// Build the SDK and write it to designated output directory.
// The OpenAPI specs first need to be loaded using [Builder.Load].
func (b *Builder) Build() error {
	if b.spec == nil {
		return fmt.Errorf("missing specs: call Load to load the specs first")
	}

	for tagName, paths := range b.pathsByTag {
		if err := b.generateResource(tagName, paths); err != nil {
			return err
		}
	}

	if err := b.writeClientFile(path.Join(b.cfg.Out, "_client.py"), slices.Collect(maps.Keys(b.pathsByTag))); err != nil {
		return err
	}

	if err := b.writeAPIVersionFile(path.Join(b.cfg.Out, "_api_version.py")); err != nil {
		return err
	}

	took := time.Since(b.start)
	slog.Info("sdk generated", slog.Duration("took", took))

	return nil
}

func join(sep string, s []string) string {
	return strings.Join(s, sep)
}
