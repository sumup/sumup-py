package builder

import (
	"bytes"
	"fmt"
	"slices"
	"strings"

	"github.com/iancoleman/strcase"

	"github.com/sumup/sumup-py/codegen/pkg/extension"
)

type eventObjectExtension struct {
	Reference string `yaml:"$ref"`
}

func (b *Builder) collectEvents() error {
	if b.spec == nil || b.spec.Webhooks == nil {
		return nil
	}

	events := make([]EventDefinition, 0, b.spec.Webhooks.Len())
	for eventType, pathItem := range b.spec.Webhooks.FromOldest() {
		if pathItem == nil || pathItem.Post == nil {
			continue
		}

		operation := pathItem.Post
		name := strings.TrimSuffix(operation.OperationId, "Webhook")
		if name == "" {
			return fmt.Errorf("webhook %q is missing an operationId", eventType)
		}

		if operation.Extensions == nil {
			return fmt.Errorf("webhook %q is missing x-object", eventType)
		}
		object, ok := extension.Get[eventObjectExtension](operation.Extensions, "x-object")
		if !ok || object.Reference == "" {
			return fmt.Errorf("webhook %q is missing x-object", eventType)
		}

		const schemaPrefix = "#/components/schemas/"
		objectSchema, ok := strings.CutPrefix(object.Reference, schemaPrefix)
		if !ok || objectSchema == "" {
			return fmt.Errorf(
				"webhook %q has unsupported x-object reference %q",
				eventType,
				object.Reference,
			)
		}

		description := strings.TrimSpace(operation.Description)
		if description == "" {
			description = strings.TrimSpace(operation.Summary)
		}

		events = append(events, EventDefinition{
			ClassName:   strcase.ToCamel(name) + "Event",
			EventType:   eventType,
			ObjectType:  strcase.ToCamel(objectSchema),
			Description: description,
		})
	}

	slices.SortFunc(events, func(a, b EventDefinition) int {
		return strings.Compare(a.ClassName, b.ClassName)
	})
	b.events = events
	return nil
}

type eventsTemplateData struct {
	Events      []EventDefinition
	ObjectTypes []string
}

func (b *Builder) writeEventsFile(filename string) error {
	objectTypes := make([]string, 0, len(b.events))
	for _, event := range b.events {
		if !slices.Contains(objectTypes, event.ObjectType) {
			objectTypes = append(objectTypes, event.ObjectType)
		}
	}
	slices.Sort(objectTypes)

	buf := bytes.NewBuffer(nil)
	if err := b.templates.ExecuteTemplate(buf, "events.py.tmpl", eventsTemplateData{
		Events:      b.events,
		ObjectTypes: objectTypes,
	}); err != nil {
		return fmt.Errorf("generate events: %w", err)
	}

	file, err := openGeneratedFile(filename)
	if err != nil {
		return err
	}
	defer func() {
		_ = file.Close()
	}()

	if _, err := file.Write(buf.Bytes()); err != nil {
		return fmt.Errorf("write events: %w", err)
	}
	return nil
}
