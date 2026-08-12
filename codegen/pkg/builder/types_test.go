package builder

import "testing"

func TestGeneratedTypesUseModernUnionSyntax(t *testing.T) {
	tests := []struct {
		name string
		got  string
		want string
	}{
		{
			name: "optional property",
			got: (&Property{
				Name:     "expires_at",
				Type:     "datetime.datetime",
				Optional: true,
			}).String(),
			want: "expires_at: datetime.datetime | None = None\n",
		},
		{
			name: "optional method parameter",
			got: (&Property{
				Name:     "status",
				Type:     "str",
				Optional: true,
			}).MethodParameterString(true),
			want: "status: str | None | NotGivenType = NOT_GIVEN",
		},
		{
			name: "enum",
			got: (&EnumDeclaration[string]{
				Name:   "Status",
				Type:   "string",
				Values: []string{"pending", "paid"},
			}).String(),
			want: "Status = typing.Literal[\"paid\", \"pending\"] | str\n",
		},
		{
			name: "one of",
			got: (&OneOfDeclaration{
				Name:    "CheckoutResponse",
				Options: []string{"CheckoutSuccess", "CheckoutAccepted"},
			}).String(),
			want: "CheckoutResponse = CheckoutSuccess | CheckoutAccepted\n",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.got != tt.want {
				t.Fatalf("generated type = %q, want %q", tt.got, tt.want)
			}
		})
	}
}

func TestInputTypeNameConvertsLegacyUnionSyntax(t *testing.T) {
	got := inputTypeName("typing.Union[Checkout, typing.Optional[list[Address]]]")
	want := "CheckoutInput | typing.Sequence[AddressInput] | None"
	if got != want {
		t.Fatalf("inputTypeName() = %q, want %q", got, want)
	}
}
