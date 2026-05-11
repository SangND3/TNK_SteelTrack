"""
Examples of pagination — both cursor (default) and page-number (admin/small lists).

Reference for:
- CursorPagination for large/changing lists (no skipped/duplicated items)
- PageNumberPagination for fixed/small lists
- Configuration in serializer or view
- Custom response shape that matches API_CONVENTION (data + meta)
"""

from __future__ import annotations

from collections import OrderedDict

from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response


# ─── Cursor pagination (default for most lists) ─────────────────────────────


class StandardCursorPagination(CursorPagination):
    """Use for lists likely to grow large or change between requests.

    Pros: stable across writes (no duplicated/skipped items on inserts)
    Cons: no random page jumps; only "next" / "prev"
    """

    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 100
    ordering = "-created_at"

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ("data", data),
            ("meta", {
                "next_cursor": self._cursor_from_url(self.get_next_link()),
                "prev_cursor": self._cursor_from_url(self.get_previous_link()),
                "has_more": self.get_next_link() is not None,
                "page_size": self.page_size,
            }),
        ]))

    @staticmethod
    def _cursor_from_url(url: str | None) -> str | None:
        """Extract just the cursor token from the full URL, for clients that
        don't want to deal with absolute URLs."""
        if not url:
            return None
        from urllib.parse import parse_qs, urlparse
        return parse_qs(urlparse(url).query).get("cursor", [None])[0]


# ─── Page-number pagination (admin / small lists) ───────────────────────────


class StandardPageNumberPagination(PageNumberPagination):
    """Use for fixed, small, admin-facing lists.

    Pros: random page jumps; total count available
    Cons: can skip/duplicate items if data changes between requests;
          COUNT(*) on large tables is slow
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ("data", data),
            ("meta", {
                "page": self.page.number,
                "page_size": self.page.paginator.per_page,
                "total": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "has_next": self.page.has_next(),
                "has_previous": self.page.has_previous(),
            }),
        ]))


# ─── Usage in a view ────────────────────────────────────────────────────────
#
# class OrderViewSet(viewsets.ModelViewSet):
#     pagination_class = StandardCursorPagination
#     ...
#
# Or globally in settings:
#
# REST_FRAMEWORK = {
#     "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardCursorPagination",
#     "PAGE_SIZE": 20,
# }


# ─── Request / response examples ────────────────────────────────────────────
#
# Cursor:
#
#   GET /api/v1/orders/?limit=20
#
#   200 OK
#   {
#     "data": [ ... 20 items ... ],
#     "meta": {
#       "next_cursor": "eyJjcmVhdGVkX2F0IjogIjIwMjYtMDUtMTBUMTA6MDA6MDBaIn0=",
#       "prev_cursor": null,
#       "has_more": true,
#       "page_size": 20
#     }
#   }
#
#   GET /api/v1/orders/?limit=20&cursor=eyJjcmVhdGVkX2F0IjogIjIwMjYtMDUtMTBUMTA6MDA6MDBaIn0=
#
#   → next page
#
#
# Page-number:
#
#   GET /api/v1/admin/users/?page=2&page_size=50
#
#   200 OK
#   {
#     "data": [ ... 50 items ... ],
#     "meta": {
#       "page": 2,
#       "page_size": 50,
#       "total": 247,
#       "total_pages": 5,
#       "has_next": true,
#       "has_previous": true
#     }
#   }
