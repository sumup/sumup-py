package extension

import (
	"github.com/pb33f/libopenapi/orderedmap"
	"gopkg.in/yaml.v3"
)

// Get extracts extension attributes from extensions.
func Get[T any](ext *orderedmap.Map[string, *yaml.Node], key string) (T, bool) {
	var empty T
	if raw, ok := ext.Get(key); ok {
		var v T
		if err := raw.Decode(&v); err != nil {
			return empty, false
		}

		return v, true
	}

	return empty, false
}

// Get extracts extension attributes from extensions, returning [def] as a default.
func GetOrDefault[T any](ext *orderedmap.Map[string, *yaml.Node], key string, def T) T {
	if val, ok := Get[T](ext, key); ok {
		return val
	}

	return def
}
