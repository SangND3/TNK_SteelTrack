# Services Layer

Business logic lives here — **not** in views, not in models.

## Rules

- One file per domain: `inventory.py`, `orders.py`, `accounts.py`
- Functions are plain Python functions, not classes (unless state is genuinely needed)
- Services call selectors for reads, ORM directly for writes
- Services raise `apps.core.exceptions.ApplicationError` subclasses on failure
- No HTTP request/response objects — services are pure domain logic

## Example

```python
# services/inventory.py

from apps.core.exceptions import ValidationError
from apps.inventory.models import SteelItem

def create_steel_item(*, name: str, quantity: int, created_by_id: int) -> SteelItem:
    if quantity <= 0:
        raise ValidationError("Số lượng phải lớn hơn 0.")
    return SteelItem.objects.create(name=name, quantity=quantity, created_by_id=created_by_id)
```
