package main

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func TestReadSDKVersion(t *testing.T) {
	t.Parallel()

	dir := t.TempDir()
	filename := filepath.Join(dir, "_version.py")
	if err := os.WriteFile(filename, []byte(`__version__ = "1.2.3"  # release`), 0o600); err != nil {
		t.Fatalf("write version file: %v", err)
	}

	version, err := readSDKVersion(filename)
	if err != nil {
		t.Fatalf("read SDK version: %v", err)
	}
	if version != "1.2.3" {
		t.Fatalf("version = %q, want 1.2.3", version)
	}
}

func TestWriteSamplesToStdout(t *testing.T) {
	t.Parallel()

	var output bytes.Buffer
	if err := writeSamples("", []byte("catalog\n"), &output); err != nil {
		t.Fatalf("write samples: %v", err)
	}
	if output.String() != "catalog\n" {
		t.Fatalf("output = %q, want catalog newline", output.String())
	}
}
