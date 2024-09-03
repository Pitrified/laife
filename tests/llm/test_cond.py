import pytest

from laife.llm.cond import (
    CompCond,
    CompOp,
    InclusionCond,
    InclusionOp,
    LogicalCond,
    LogicalOp,
)


def test_comp_cond() -> None:
    # Test equality condition
    cond = CompCond("age", CompOp.EQ, 30)
    assert cond.to_dict() == {"age": 30}

    # Test greater than condition
    cond = CompCond("age", CompOp.GT, 30)
    assert cond.to_dict() == {"age": {"$gt": 30}}


def test_inclusion_cond() -> None:
    # Test inclusion condition
    cond = InclusionCond("name", InclusionOp.IN, "John", "Jane")
    assert cond.to_dict() == {"name": {"$in": ["John", "Jane"]}}

    # Test exclusion condition
    cond = InclusionCond("name", InclusionOp.NIN, "John", "Jane")
    assert cond.to_dict() == {"name": {"$nin": ["John", "Jane"]}}


def test_logical_cond() -> None:
    # Test logical AND condition
    comp_cond1 = CompCond("age", CompOp.GT, 30)
    comp_cond2 = CompCond("name", CompOp.EQ, "John")
    logical_cond = LogicalCond(LogicalOp.AND, comp_cond1, comp_cond2)
    assert logical_cond.to_dict() == {"$and": [{"age": {"$gt": 30}}, {"name": "John"}]}

    # Test logical OR condition
    inclusion_cond1 = InclusionCond("name", InclusionOp.IN, "John", "Jane")
    inclusion_cond2 = InclusionCond("age", InclusionOp.NIN, 20, 30)
    logical_cond = LogicalCond(LogicalOp.OR, inclusion_cond1, inclusion_cond2)
    assert logical_cond.to_dict() == {
        "$or": [{"name": {"$in": ["John", "Jane"]}}, {"age": {"$nin": [20, 30]}}]
    }


def test_inclusion_cond_with_empty_values() -> None:
    # Test inclusion condition with empty values
    with pytest.raises(ValueError):
        cond = InclusionCond("name", InclusionOp.IN)


def test_logical_cond_with_no_and_single_condition() -> None:
    # Test logical AND condition with a single condition
    with pytest.raises(ValueError):
        comp_cond = CompCond("age", CompOp.GT, 30)
        logical_cond = LogicalCond(LogicalOp.AND, comp_cond)

    # Test logical OR condition with no conditions
    with pytest.raises(ValueError):
        logical_cond = LogicalCond(LogicalOp.OR)
