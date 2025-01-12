"""Utility decorators"""
from typing import Type, TypeVar, Any
from functools import wraps
import threading

T = TypeVar('T')

def singleton(cls: Type[T]) -> Type[T]:
    """Thread-safe singleton decorator"""
    instances = {}
    lock = threading.Lock()

    @wraps(cls)
    def get_instance(*args: Any, **kwargs: Any) -> T:
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance 