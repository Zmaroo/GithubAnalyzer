"""Type stubs for neo4j package."""

from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union, overload

T = TypeVar("T")

class Driver:
    def __init__(self, uri: str, auth: tuple[str, str], **kwargs: Any) -> None: ...
    def session(self, database: Optional[str] = None, **kwargs: Any) -> Session: ...
    def close(self) -> None: ...

class Session:
    def __init__(self, driver: Driver, database: Optional[str] = None) -> None: ...
    def run(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Result: ...
    def close(self) -> None: ...
    def __enter__(self) -> Session: ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...

class Result:
    def single(self) -> Optional[Record]: ...
    def data(self) -> List[Dict[str, Any]]: ...
    def consume(self) -> ResultSummary: ...
    def peek(self) -> Optional[Record]: ...
    def graph(self) -> Graph: ...

class Record:
    def __init__(self, values: List[Any], keys: List[str]) -> None: ...
    def get(self, key: str, default: Optional[T] = None) -> Optional[T]: ...
    def __getitem__(self, key: Union[str, int]) -> Any: ...

class Transaction:
    def run(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Result: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...

class ResultSummary:
    counters: Counters
    def __init__(self) -> None: ...

class Counters:
    nodes_created: int
    nodes_deleted: int
    relationships_created: int
    relationships_deleted: int
    properties_set: int
    labels_added: int
    labels_removed: int
    indexes_added: int
    indexes_removed: int
    constraints_added: int
    constraints_removed: int

class Graph:
    nodes: List[Node]
    relationships: List[Relationship]

class Node:
    id: int
    labels: List[str]
    properties: Dict[str, Any]

class Relationship:
    id: int
    type: str
    properties: Dict[str, Any]
    start_node: Node
    end_node: Node

class GraphDatabase:
    @staticmethod
    def driver(uri: str, auth: tuple[str, str], **kwargs: Any) -> Driver: ...
