package main

import (
	"fmt"
	"os"

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

			spec, err := loadOpenAPIDocument(specs)
			if err != nil {
				return err
			}

			builder := builder.New(builder.Config{
				Out: out,
			})

			if err := builder.Load(spec); err != nil {
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
