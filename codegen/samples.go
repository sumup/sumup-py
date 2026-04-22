package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"

	"github.com/urfave/cli/v2"
)

var versionPattern = regexp.MustCompile(`(?m)^__version__\s*=\s*["']([^"']+)["']`)

func Samples() *cli.Command {
	var out string
	var sdkVersion string
	var sdkVersionFile string
	return &cli.Command{
		Name:  "samples",
		Usage: "Generate Python code samples as a JSON catalog",
		Args:  true,
		Action: func(c *cli.Context) error {
			if !c.Args().Present() {
				return fmt.Errorf("empty argument, path to openapi specs expected")
			}
			if sdkVersion == "" && sdkVersionFile != "" {
				version, err := readSDKVersion(sdkVersionFile)
				if err != nil {
					return err
				}
				sdkVersion = version
			}
			if sdkVersion == "" {
				return fmt.Errorf("missing SDK version: set --sdk-version or --sdk-version-file")
			}

			generator, err := loadBuilder(c.Args().First(), "")
			if err != nil {
				return err
			}
			catalog, err := generator.Samples(sdkVersion)
			if err != nil {
				return fmt.Errorf("generate samples: %w", err)
			}

			encoded, err := json.MarshalIndent(catalog, "", "  ")
			if err != nil {
				return fmt.Errorf("encode samples: %w", err)
			}
			encoded = append(encoded, '\n')

			stdout := c.App.Writer
			if stdout == nil {
				stdout = os.Stdout
			}
			return writeSamples(out, encoded, stdout)
		},
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:        "out",
				Aliases:     []string{"o"},
				Usage:       "path of the output JSON file (defaults to stdout)",
				Destination: &out,
			},
			&cli.StringFlag{
				Name:        "sdk-version",
				Usage:       "SumUp Python SDK version represented by the samples",
				Destination: &sdkVersion,
			},
			&cli.PathFlag{
				Name:        "sdk-version-file",
				Usage:       "Python source file containing the SDK __version__ assignment",
				Destination: &sdkVersionFile,
			},
		},
	}
}

func writeSamples(out string, encoded []byte, stdout io.Writer) error {
	if out == "" {
		if _, err := stdout.Write(encoded); err != nil {
			return fmt.Errorf("write samples: %w", err)
		}
		return nil
	}

	dir := filepath.Dir(out)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return fmt.Errorf("create output directory %q: %w", dir, err)
	}
	if err := os.WriteFile(out, encoded, 0o644); err != nil {
		return fmt.Errorf("write samples %q: %w", out, err)
	}
	return nil
}

func readSDKVersion(filename string) (string, error) {
	source, err := os.ReadFile(filename)
	if err != nil {
		return "", fmt.Errorf("read SDK version file: %w", err)
	}
	match := versionPattern.FindSubmatch(source)
	if len(match) != 2 {
		return "", fmt.Errorf("find SDK version in %q", filename)
	}
	return string(match[1]), nil
}
