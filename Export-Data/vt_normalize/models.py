from pydantic import BaseModel


class CompanyName(BaseModel):
    """
    Represents a clustered company name with its canonical form, aliases, and occurrence count.

    Attributes:
        canonical_name: The standardized, cleaned company name (brand identifier)
        aliases: List of raw name variations that map to this canonical name
        count: Total number of occurrences across all aliases
    """
    canonical_name: str
    aliases: list[str] = []
    count: int = 0
