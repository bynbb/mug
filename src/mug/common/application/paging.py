"""Common.Application: simple paging primitives.

Lightweight, framework-agnostic helpers for pagination. Handlers can return a
`Page[T]` to Presentation, which can render consistently.

Usage:
    from mug.common.application.paging import PageRequest, paginate

    req = PageRequest(page=2, size=10)
    page = paginate(range(53), req)   # works with Sequences and Iterables
    assert page.page == 2
    assert page.size == 10
    assert page.total == 53
    assert page.items == list(range(10, 20))
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Generic, Iterable, Iterator, List, Sequence, Tuple, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PageRequest:
    """Client paging request.

    Args:
        page: 1-based page number.
        size: page size (items per page).
    """
    page: int = 1
    size: int = 50

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be >= 1")
        if self.size < 1 or self.size > 1000:
            raise ValueError("size must be in [1, 1000]")


@dataclass(frozen=True)
class Page(Generic[T]):
    """A single page of items with total count and page metadata."""
    items: List[T]
    total: int
    page: int         # 1-based
    size: int         # page size

    @property
    def pages(self) -> int:
        """Total number of pages (>= 1 when total > 0, else 0)."""
        return ceil(self.total / self.size) if self.total > 0 else 0

    @property
    def has_prev(self) -> bool:
        return self.page > 1 and self.total > 0

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def first_index(self) -> int:
        """0-based index of first item on this page within the full result set."""
        return (self.page - 1) * self.size

    @property
    def last_index(self) -> int:
        """0-based index of last item on this page within the full result set (inclusive)."""
        return min(self.first_index + self.size, self.total) - 1 if self.total else -1

    def map(self, fn) -> "Page":
        """Map items to another type while preserving paging metadata."""
        return Page(items=[fn(x) for x in self.items], total=self.total, page=self.page, size=self.size)


def paginate(data: Sequence[T] | Iterable[T], request: PageRequest) -> Page[T]:
    """Paginate either a Sequence (supports slicing) or a generic Iterable.

    - For Sequences: O(1) slicing and O(1) total via len().
    - For Iterables: consumes the iterable to compute total and collect the current page.
      This is O(n) and should be used for small/finite iterables only.

    Args:
        data: the collection to paginate.
        request: paging request (1-based page, size).

    Returns:
        Page[T]
    """
    if isinstance(data, Sequence):
        return _paginate_sequence(data, request)
    return _paginate_iterable(iter(data), request)


def _paginate_sequence(seq: Sequence[T], req: PageRequest) -> Page[T]:
    total = len(seq)
    start = (req.page - 1) * req.size
    end = start + req.size
    if start >= total:
        # empty page beyond the end
        return Page(items=[], total=total, page=req.page, size=req.size)
    items = list(seq[start:end])
    return Page(items=items, total=total, page=req.page, size=req.size)


def _paginate_iterable(it: Iterator[T], req: PageRequest) -> Page[T]:
    """Consume an iterator to compute total and slice the desired page."""
    start = (req.page - 1) * req.size
    end = start + req.size

    items: List[T] = []
    total = 0

    # Single pass: collect only requested window, but still count total.
    for idx, item in enumerate(it):
        if start <= idx < end:
            items.append(item)
        total += 1

    # If requested page is out of range, return empty with accurate total.
    if start >= total:
        items = []

    return Page(items=items, total=total, page=req.page, size=req.size)