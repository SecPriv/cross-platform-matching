from dataclasses import dataclass
from typing import Optional

@dataclass(kw_only=True)
class Entitlements:

    path: Optional[str] = None
    raw_data: Optional[dict] = None
    universal_links: Optional[list[str]] = None
    has_multicast: Optional[bool] = None
    entitlements: Optional[list] = None