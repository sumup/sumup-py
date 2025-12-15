class _OpenStrEnum(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return handler(str)


class _OpenIntEnum(int):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return handler(int)


class _OpenFloatEnum(float):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return handler(float)
