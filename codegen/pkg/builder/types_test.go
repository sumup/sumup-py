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
			name: "required property",
			got: (&Property{
				Name: "checkout_id",
				Type: "str",
			}).String(),
			want: "checkout_id: str\n",
		},
		{
			name: "required nullable property",
			got: (&Property{
				Name:     "card_type",
				Type:     "GetReaderCheckoutResponseDataCardType",
				Nullable: true,
			}).String(),
			want: "card_type: GetReaderCheckoutResponseDataCardType | None\n",
		},
		{
			name: "required nullable aliased property",
			got: (&Property{
				Name:           "card_type",
				SerializedName: "cardType",
				Type:           "str",
				Nullable:       true,
			}).String(),
			want: "card_type: str | None = pydantic.Field(serialization_alias=\"cardType\", validation_alias=pydantic.AliasChoices(\"cardType\", \"card_type\"))\n",
		},
		{
			name: "required nullable typed dict field",
			got: (&Property{
				Name:     "installments",
				Type:     "int",
				Nullable: true,
			}).TypedDictFieldString(),
			want: "installments: typing_extensions.Required[int | None]",
		},
		{
			name: "required nullable method parameter",
			got: (&Property{
				Name:     "card_type",
				Type:     "str",
				Nullable: true,
			}).MethodParameterString(true),
			want: "card_type: str | None",
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
