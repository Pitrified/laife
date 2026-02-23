"""Test cond module."""

import pytest

from laife.llm_services.vectorstores.cond import CompCond
from laife.llm_services.vectorstores.cond import CompOp
from laife.llm_services.vectorstores.cond import InclusionCond
from laife.llm_services.vectorstores.cond import InclusionOp
from laife.llm_services.vectorstores.cond import LogicalCond
from laife.llm_services.vectorstores.cond import LogicalOp


def test_comp_cond() -> None:
    """Verify CompCond outputs correct dicts for EQ and GT operators."""
    # Test equality condition
    cond = CompCond("age", CompOp.EQ, 30)
    assert cond.to_dict() == {"age": 30}

    # Test greater than condition
    cond = CompCond("age", CompOp.GT, 30)
    assert cond.to_dict() == {"age": {"$gt": 30}}


def test_inclusion_cond() -> None:
    """Check InclusionCond produces correct $in and $nin mappings."""
    # Test inclusion condition
    cond = InclusionCond("name", InclusionOp.IN, "John", "Jane")
    assert cond.to_dict() == {"name": {"$in": ["John", "Jane"]}}

    # Test exclusion condition
    cond = InclusionCond("name", InclusionOp.NIN, "John", "Jane")
    assert cond.to_dict() == {"name": {"$nin": ["John", "Jane"]}}


def test_logical_cond() -> None:
    """Ensure LogicalCond composes sub-conditions with $and and $or."""
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
    """Raise ValueError when InclusionCond is created without values."""
    # Test inclusion condition with empty values
    msg = "Values cannot be empty."
    with pytest.raises(ValueError, match=msg):
        _ = InclusionCond("name", InclusionOp.IN)


def test_logical_cond_with_no_and_single_condition() -> None:
    """Validate LogicalCond enforces minimum condition counts for operators."""
    # Test logical AND condition with a single condition
    comp_cond = CompCond("age", CompOp.GT, 30)
    msg = "Conditions must be more than one."
    with pytest.raises(ValueError, match=msg):
        _ = LogicalCond(LogicalOp.AND, comp_cond)

    # Test logical OR condition with no conditions
    msg = "Conditions cannot be empty."
    with pytest.raises(ValueError, match=msg):
        _ = LogicalCond(LogicalOp.OR)
