package builder

import (
	"testing"

	"github.com/pb33f/libopenapi/datamodel/high/base"
)

func TestSchemaIsNullable(t *testing.T) {
	t.Parallel()

	nullable := true
	tests := []struct {
		name   string
		schema *base.Schema
		want   bool
	}{
		{name: "nil schema", want: false},
		{name: "not nullable", schema: &base.Schema{Type: []string{"string"}}, want: false},
		{
			name:   "openapi 3.0 nullable",
			schema: &base.Schema{Type: []string{"string"}, Nullable: &nullable},
			want:   true,
		},
		{
			name:   "openapi 3.1 null type",
			schema: &base.Schema{Type: []string{"string", "null"}},
			want:   true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			if got := schemaIsNullable(tt.schema); got != tt.want {
				t.Fatalf("schemaIsNullable() = %v, want %v", got, tt.want)
			}
		})
	}
}
