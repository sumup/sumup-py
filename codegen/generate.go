package main

import (
	"errors"
	"fmt"
	"os"

	"github.com/pb33f/libopenapi"
	"github.com/urfave/cli/v2"

	"github.com/sumup/sumup-py/codegen/pkg/builder"
)

func Generate() *cli.Command {
	var (
		out string
	)

	return &cli.Command{
		Name:  "generate",
		Usage: "Generate SDK",
		Args:  true,
		Action: func(c *cli.Context) error {
			if !c.Args().Present() {
				return fmt.Errorf("empty argument, path to openapi specs expected")
			}

			specs := c.Args().First()

			if err := os.MkdirAll(out, os.ModePerm); err != nil {
				return fmt.Errorf("create output directory %q: %w", out, err)
			}

			spec, err := os.ReadFile(specs)
			if err != nil {
				return fmt.Errorf("read specs: %w", err)
			}

			doc, err := libopenapi.NewDocument(spec)
			if err != nil {
				return fmt.Errorf("load openapi document: %w", err)
			}

			model, errs := doc.BuildV3Model()
			if len(errs) > 0 {
				return fmt.Errorf("build openapi v3 model: %w", errors.Join(errs...))
			}

			builder := builder.New(builder.Config{
				Out: out,
			})

			if err := builder.Load(&model.Model); err != nil {
				return fmt.Errorf("load spec: %w", err)
			}

			if err := builder.Build(); err != nil {
				return fmt.Errorf("build sdk: %w", err)
			}

			return nil
		},
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:        "out",
				Aliases:     []string{"o"},
				Usage:       "path of the output directory",
				Required:    false,
				Destination: &out,
				Value:       "./",
			},
		},
	}
}
