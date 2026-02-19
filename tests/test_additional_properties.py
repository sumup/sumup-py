from sumup.types import Problem


def test_problem_collects_and_serializes_additional_properties():
    payload = {
        "type": "https://developer.sumup.com/problem/not-found",
        "title": "Requested resource couldn't be found.",
        "foo": "bar",
        "nested": {"answer": 42},
    }

    problem = Problem.model_validate(payload)

    assert problem.type == payload["type"]
    assert problem.title == payload["title"]
    assert problem.additional_properties == {
        "foo": "bar",
        "nested": {"answer": 42},
    }

    dumped = problem.model_dump()
    assert dumped["foo"] == "bar"
    assert dumped["nested"] == {"answer": 42}
    assert "additional_properties" not in dumped
