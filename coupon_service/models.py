from dataclasses import dataclass, asdict
from typing import Dict, Any
from datetime import datetime
from coupon_service.utils.constants import CouponStatus, SystemFields, DefaultValues

@dataclass
class Coupon:
    """
    A dataclass representing a coupon object within our application's business logic.
    """
    coupon_code: str
    type: str
    description: str
    metadata: Dict[str, Any]
    status: str = CouponStatus.ACTIVE
    _id: str = None
    # System fields managed by the server layer
    _created_at: datetime = None
    _modified_at: datetime = None
    _created_by: str = DefaultValues.FLOBOT
    _modified_by: str = DefaultValues.FLOBOT

    def to_dict(self) -> Dict[str, Any]:
        """Converts the coupon object to a dictionary for DB storage."""
        data = asdict(self)
        # Convert datetime objects to ISO format strings for MongoDB
        if data.get(SystemFields.CREATED_AT) and isinstance(data[SystemFields.CREATED_AT], datetime):
            data[SystemFields.CREATED_AT] = data[SystemFields.CREATED_AT].isoformat()
        if data.get(SystemFields.MODIFIED_AT) and isinstance(data[SystemFields.MODIFIED_AT], datetime):
            data[SystemFields.MODIFIED_AT] = data[SystemFields.MODIFIED_AT].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Coupon":
        """Creates a Coupon object from a dictionary (e.g., from MongoDB)."""
        created_at = data.get(SystemFields.CREATED_AT)
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        modified_at = data.get(SystemFields.MODIFIED_AT)
        if isinstance(modified_at, str):
            modified_at = datetime.fromisoformat(modified_at)

        return cls(
            _id=data.get(SystemFields.ID),
            coupon_code=data.get("coupon_code"),
            type=data.get("type"),
            description=data.get("description"),
            metadata=data.get("metadata"),
            status=data.get("status"),
            _created_at=created_at,
            _modified_at=modified_at,
            _created_by=data.get(SystemFields.CREATED_BY, DefaultValues.FLOBOT),
            _modified_by=data.get(SystemFields.MODIFIED_BY, DefaultValues.FLOBOT),
        )
