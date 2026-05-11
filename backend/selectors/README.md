# Selectors Layer

Read-only database queries. Return QuerySets or typed values.

## Rules

- One file per domain: `inventory.py`, `orders.py`
- Functions return QuerySet or a concrete value — never HTTP responses
- No side effects (no writes, no emails, no tasks)
- Apply `.select_related()` / `.prefetch_related()` here — never in views

## Example

```python
# selectors/inventory.py

from django.db.models import QuerySet
from apps.inventory.models import SteelItem

def get_active_steel_items() -> QuerySet[SteelItem]:
    return SteelItem.objects.filter(is_active=True).select_related("category").order_by("name")
```
