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
from typing import Literal, Self

Field = str
LiteralValue = str | int | float | bool


class CompOp(Enum):
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
        self.field = field
        self.value = value
        self.operator = operator

    def to_dict(
        self,
    ) -> dict[Field, LiteralValue] | dict[Field, dict[CompOpLit, LiteralValue]]:
        if self.operator == CompOp.EQ:
            return {self.field: self.value}
        return {self.field: {self.operator.value: self.value}}


class InclusionOp(Enum):
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
        if len(values) == 0:
            raise ValueError("Values cannot be empty.")
        self.field = field
        self.values = values
        self.operator = operator

    def to_dict(self) -> dict[Field, dict[InclusionOpLit, list[LiteralValue]]]:
        return {self.field: {self.operator.value: list(self.values)}}


class LogicalOp(Enum):
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
        if len(conditions) == 0:
            raise ValueError("Conditions cannot be empty.")
        elif len(conditions) == 1:
            raise ValueError("Conditions must be more than one.")
        self.conditions = conditions
        self.operator = operator

    def to_dict(self) -> dict[LogicalOpLit, list]:
        return {self.operator.value: [c.to_dict() for c in self.conditions]}
