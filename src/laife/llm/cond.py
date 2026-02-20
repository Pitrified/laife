"""Module for NoSQL compatible conditionals.

.venv/lib/python3.11/site-packages/chromadb/types.py

```python
# Extension
Field = str
# Metadata Query Grammar
LiteralValue = Union[str, int, float, bool]
LogicalOperator = Union[Literal["$and"], Literal["$or"]]
WhereOperator = Union[
    Literal["$gt"],
    Literal["$gte"],
    Literal["$lt"],
    Literal["$lte"],
    Literal["$ne"],
    Literal["$eq"],
]
InclusionExclusionOperator = Union[Literal["$in"], Literal["$nin"]]
OperatorExpression = Union[
    Dict[Union[WhereOperator, LogicalOperator], LiteralValue],
    Dict[InclusionExclusionOperator, List[LiteralValue]],
]

Where = Dict[
    Union[str, LogicalOperator],
    Union[LiteralValue, OperatorExpression, List["Where"]]
]

WhereDocumentOperator = Union[
    Literal["$contains"],
    Literal["$not_contains"],
    LogicalOperator
]
WhereDocument = Dict[WhereDocumentOperator, Union[str, List["WhereDocument"]]]
```
"""

from enum import Enum
from typing import Literal
from typing import Self

Field = str
LiteralValue = str | int | float | bool


class CompOp(Enum):
    """Comparison operators for conditional expressions."""

    EQ = "$eq"
    NE = "$ne"
    GT = "$gt"
    GTE = "$gte"
    LT = "$lt"
    LTE = "$lte"


CompOpLit = Literal["$eq", "$ne", "$gt", "$gte", "$lt", "$lte"]


class CompCond:
    """Class for NoSQL compatible where operations."""

    def __init__(
        self,
        field: Field,
        operator: CompOp,
        value: LiteralValue,
    ) -> None:
        """Initialize a comparison condition for a field."""
        self.field = field
        self.value = value
        self.operator = operator

    def to_dict(
        self,
    ) -> dict[Field, LiteralValue] | dict[Field, dict[CompOpLit, LiteralValue]]:
        """Return the condition formatted as a dictionary."""
        if self.operator == CompOp.EQ:
            return {self.field: self.value}
        return {self.field: {self.operator.value: self.value}}


class InclusionOp(Enum):
    """Operators for inclusion/exclusion checks."""

    IN = "$in"
    NIN = "$nin"


InclusionOpLit = Literal["$in", "$nin"]


class InclusionCond:
    """Class for NoSQL compatible inclusion/exclusion operations."""

    def __init__(
        self,
        field: Field,
        operator: InclusionOp,
        *values: LiteralValue,
    ) -> None:
        """Initialize an inclusion/exclusion condition with values."""
        if len(values) == 0:
            msg = "Values cannot be empty."
            raise ValueError(msg)
        self.field = field
        self.values = values
        self.operator = operator

    def to_dict(self) -> dict[Field, dict[InclusionOpLit, list[LiteralValue]]]:
        """Return the inclusion condition as a dictionary."""
        return {self.field: {self.operator.value: list(self.values)}}


class LogicalOp(Enum):
    """Logical combinators for conditions."""

    AND = "$and"
    OR = "$or"


LogicalOpLit = Literal["$and", "$or"]


class LogicalCond:
    """Class for NoSQL compatible logical operations."""

    def __init__(
        self,
        operator: LogicalOp,
        *conditions: CompCond | InclusionCond | Self,
    ) -> None:
        """Initialize a logical condition composed of sub-conditions."""
        if len(conditions) == 0:
            msg = "Conditions cannot be empty."
            raise ValueError(msg)
        if len(conditions) == 1:
            msg = "Conditions must be more than one."
            raise ValueError(msg)
        self.conditions = conditions
        self.operator = operator

    def to_dict(self) -> dict[LogicalOpLit, list]:
        """Return the logical condition as a dict combining sub-conditions."""
        return {self.operator.value: [c.to_dict() for c in self.conditions]}
