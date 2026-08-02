package builder

import (
	"reflect"
	"testing"

	"github.com/pb33f/libopenapi"
)

func TestCollectEvents(t *testing.T) {
	document, err := libopenapi.NewDocument([]byte(`{
  "openapi": "3.1.0",
  "info": {"title": "Events", "version": "1.0.0"},
  "paths": {},
  "components": {
    "schemas": {
      "Member": {"type": "object"},
      "Reader": {"type": "object"}
    }
  },
  "webhooks": {
    "readers.created": {
      "post": {
        "operationId": "ReaderCreatedWebhook",
        "description": "Sent when a reader is paired.",
        "responses": {"2XX": {"description": "Acknowledged"}},
        "x-object": {"$ref": "#/components/schemas/Reader"}
      }
    },
    "members.updated": {
      "post": {
        "operationId": "MemberUpdatedWebhook",
        "description": "Sent when a member changes.",
        "responses": {"2XX": {"description": "Acknowledged"}},
        "x-object": {"$ref": "#/components/schemas/Member"}
      }
    }
  }
}`))
	if err != nil {
		t.Fatalf("load document: %v", err)
	}
	model, err := document.BuildV3Model()
	if err != nil {
		t.Fatalf("build model: %v", err)
	}

	builder := New(Config{})
	if err := builder.Load(&model.Model); err != nil {
		t.Fatalf("load builder: %v", err)
	}

	want := []EventDefinition{
		{
			ClassName:   "MemberUpdatedEvent",
			EventType:   "members.updated",
			ObjectType:  "Member",
			Description: "Sent when a member changes.",
		},
		{
			ClassName:   "ReaderCreatedEvent",
			EventType:   "readers.created",
			ObjectType:  "Reader",
			Description: "Sent when a reader is paired.",
		},
	}
	if !reflect.DeepEqual(builder.events, want) {
		t.Fatalf("events mismatch:\n got: %#v\nwant: %#v", builder.events, want)
	}
}
