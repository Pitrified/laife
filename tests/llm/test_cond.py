"""Tests for the cond module (now backed by llm_core.vectorstores.cond)."""

from llm_core.vectorstores.cond import CompCond
from llm_core.vectorstores.cond import CompOp
from llm_core.vectorstores.cond import InclusionCond
from llm_core.vectorstores.cond import InclusionOp
from llm_core.vectorstores.cond import LogicalCond
from llm_core.vectorstores.cond import LogicalOp


def test_comp_cond() -> None:
    """CompCond stores field, op, and value correctly."""
    cond = CompCond("age", CompOp.EQ, 30)
    assert cond.field == "age"
    assert cond.op == CompOp.EQ
    assert cond.value == 30

    cond_gt = CompCond("age", CompOp.GT, 30)
    assert cond_gt.op == CompOp.GT


def test_inclusion_cond() -> None:
    """InclusionCond stores field, op, and values list correctly."""
    cond = InclusionCond("name", InclusionOp.IN, ["John", "Jane"])
    assert cond.field == "name"
    assert cond.op == InclusionOp.IN
    assert cond.values == ["John", "Jane"]

    cond_nin = InclusionCond("name", InclusionOp.NIN, ["John", "Jane"])
    assert cond_nin.op == InclusionOp.NIN


def test_logical_cond() -> None:
    """LogicalCond composes sub-conditions with AND and OR operators."""
    comp_cond1 = CompCond("age", CompOp.GT, 30)
    comp_cond2 = CompCond("name", CompOp.EQ, "John")
    logical_cond = LogicalCond(LogicalOp.AND, [comp_cond1, comp_cond2])
    assert logical_cond.op == LogicalOp.AND
    assert logical_cond.children == [comp_cond1, comp_cond2]

    logical_or = LogicalCond(LogicalOp.OR, [comp_cond1, comp_cond2])
    assert logical_or.op == LogicalOp.OR


def test_logical_cond_via_operator_overloading() -> None:
    """Operator & produces a flat AND condition."""
    a = CompCond("age", CompOp.GT, 30)
    b = CompCond("name", CompOp.EQ, "John")
    result = a & b
    assert isinstance(result, LogicalCond)
    assert result.op == LogicalOp.AND
    assert result.children == [a, b]


def test_logical_cond_or_via_operator_overloading() -> None:
    """Operator | produces a flat OR condition."""
    a = InclusionCond("name", InclusionOp.IN, ["John", "Jane"])
    b = CompCond("age", CompOp.GT, 20)
    result = a | b
    assert isinstance(result, LogicalCond)
    assert result.op == LogicalOp.OR
    assert result.children == [a, b]
