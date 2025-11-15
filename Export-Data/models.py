"""
Pydantic models for Peru Frozen Fruit Export Data validation and enrichment.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
import re


class ProductFormat(BaseModel):
    """Structured product format information extracted from descriptions."""

    format_type: Optional[Literal[
        "chunks", "cubes", "slices", "halves", "puree", "pulp", "whole",
        "strips", "iqf", "broken_pieces", "concentrate", "juice", "unknown"
    ]] = Field(None, description="Product format/cut type")

    size_mm: Optional[str] = Field(None, description="Standardized size in mm (e.g., '20x20', '10x10')")

    @field_validator('size_mm', mode='before')
    @classmethod
    def standardize_size(cls, v):
        """Standardize size format."""
        if v and isinstance(v, str):
            # Extract numbers from patterns like "20X20MM" or "20x20"
            match = re.search(r'(\d+)\s*[xX]\s*(\d+)', v)
            if match:
                return f"{match.group(1)}x{match.group(2)}"
        return v


class ProductClassification(BaseModel):
    """Product classification and standards."""

    is_organic: bool = Field(default=False, description="Whether product is certified organic")

    is_conventional: bool = Field(default=False, description="Whether product is conventional (non-organic)")

    is_iqf: bool = Field(default=False, description="Individually Quick Frozen")

    is_aseptic: bool = Field(default=False, description="Aseptic processing (not frozen, shelf-stable)")

    certification: Optional[Literal["organic", "conventional", "unknown"]] = Field(
        default="unknown", description="Certification type"
    )

    @field_validator('certification', mode='after')
    @classmethod
    def determine_certification(cls, v, info):
        """Automatically determine certification based on flags."""
        if info.data.get('is_organic'):
            return "organic"
        elif info.data.get('is_conventional'):
            return "conventional"
        return v or "unknown"


class FruitProduct(BaseModel):
    """Main fruit product information."""

    fruit_name: Literal[
        "mango", "pineapple", "strawberry", "blueberry", "papaya", "avocado",
        "pomegranate", "lucuma", "passion_fruit", "golden_berry", "camu_camu",
        "soursop", "cherimoya", "pitaya", "acai", "banana", "raspberry",
        "cherry", "peach", "grape", "orange", "mix", "other", "unknown"
    ] = Field(description="Type of fruit")

    variety: Optional[str] = Field(None, description="Fruit variety (e.g., Kent, Edward, Haden)")

    product_format: ProductFormat = Field(default_factory=ProductFormat, description="Product format details")

    classification: ProductClassification = Field(
        default_factory=ProductClassification, description="Product classification"
    )


class ExportRecord(BaseModel):
    """Complete export record with all original and enriched data."""

    # Original fields
    hts_code: str = Field(alias="HTS Code")
    hts_code_description: str = Field(alias="HTS Code Description")
    customs: str = Field(alias="Customs")
    dua_dam: str = Field(alias="DUA / DAM")
    date: datetime = Field(alias="Date")
    tax_id: int = Field(alias="Tax ID")
    exporter: str = Field(alias="Exporter")
    importer: Optional[str] = Field(None, alias="Importer")

    # Weight and quantity
    gross_kg: Optional[float] = Field(None, alias="Gross kg")
    net_kg: Optional[float] = Field(None, alias="Net kg")
    qty_1: Optional[float] = Field(None, alias="Qty 1")
    unit_1: Optional[str] = Field(None, alias="Unit 1")
    qty_2: Optional[float] = Field(None, alias="Qty 2")
    unit_2: Optional[str] = Field(None, alias="Unit 2")

    # Pricing (USD)
    usd_fob_total: Optional[float] = Field(None, alias="U$ FOB Tot")
    usd_fob_unit_1: Optional[float] = Field(None, alias="U$ FOB Unit 1")
    usd_fob_unit_2: Optional[float] = Field(None, alias="U$ FOB Unit 2")

    # Destination and logistics
    destination_country: Optional[str] = Field(None, alias="Destination Country")
    destination_port: Optional[str] = Field(None, alias="Destination Port")
    last_port: Optional[str] = Field(None, alias="Last Port")
    via: Optional[str] = Field(None, alias="Via")
    port_agent: Optional[str] = Field(None, alias="Port Agent")
    customs_agent: Optional[str] = Field(None, alias="Customs Agent")
    shipping_line: Optional[str] = Field(None, alias="Shipping Line")
    forwarding_agent_origin: Optional[str] = Field(None, alias="Forwarding Agent(Origin)")
    forwarding_agent_destination: Optional[str] = Field(None, alias="Forwarding Agent(Destination)")
    channel: Optional[str] = Field(None, alias="Channel")

    # Descriptions
    commercial_description: str = Field(alias="Commercial Description")
    description1: Optional[str] = Field(None, alias="Description1")
    description2: Optional[str] = Field(None, alias="Description2")
    description3: Optional[str] = Field(None, alias="Description3")
    description4: Optional[str] = Field(None, alias="Description4")
    description5: Optional[str] = Field(None, alias="Description5")

    # Enriched structured data
    product: Optional[FruitProduct] = Field(None, description="Parsed and structured product information")

    # Computed fields - KEY METRICS
    net_weight_mt: Optional[float] = Field(None, description="Net weight in metric tons")
    usd_per_mt_fob: Optional[float] = Field(None, description="USD per metric ton FOB")

    class Config:
        populate_by_name = True

    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Parse date string to datetime."""
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

    def model_post_init(self, __context):
        """Calculate computed fields after initialization."""
        # Calculate weight in metric tons
        if self.net_kg:
            self.net_weight_mt = round(self.net_kg / 1000, 3)

        # Calculate USD per MT FOB
        if self.usd_fob_total and self.net_weight_mt and self.net_weight_mt > 0:
            self.usd_per_mt_fob = round(self.usd_fob_total / self.net_weight_mt, 2)


class ProductSummary(BaseModel):
    """Summary by Fruit → Format → Size with total MT and USD/MT."""

    fruit_name: str
    format_type: str
    size_mm: Optional[str]
    certification: str
    total_mt: float = Field(description="Total metric tons exported")
    avg_usd_per_mt: float = Field(description="Average USD per metric ton FOB")
    record_count: int = Field(description="Number of export records")
    total_fob_usd: float = Field(description="Total FOB value in USD")

    class Config:
        json_schema_extra = {
            "example": {
                "fruit_name": "mango",
                "format_type": "chunks",
                "size_mm": "20x20",
                "certification": "organic",
                "total_mt": 500.5,
                "avg_usd_per_mt": 2800.00,
                "record_count": 45,
                "total_fob_usd": 1401400.00
            }
        }


class ExportDataSummary(BaseModel):
    """Summary statistics for export data by product hierarchy."""

    total_records: int
    date_range_start: datetime
    date_range_end: datetime
    total_mt: float = Field(description="Total metric tons exported")
    total_fob_usd: float = Field(description="Total FOB value in USD")
    avg_usd_per_mt: float = Field(description="Overall average USD per MT")

    # Hierarchical summaries: Fruit → Format → Size
    by_fruit: dict[str, float] = Field(description="Total MT by fruit type")
    by_format: dict[str, float] = Field(description="Total MT by format type")
    by_size: dict[str, float] = Field(description="Total MT by size")

    # Detailed product summaries
    product_summaries: list[ProductSummary] = Field(
        description="Detailed summaries grouped by Fruit → Format → Size"
    )

    unique_exporters: int
    unique_destination_countries: int
    top_destinations: dict[str, float] = Field(description="Top destinations by MT")
