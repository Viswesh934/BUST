from typing import List, Optional
from pydantic import BaseModel, Field


class ObjectionCard(BaseModel):
    id: str = Field(description="Unique identifier for the card, e.g. card_1")
    category: str = Field(
        description="Category: 'Pricing / Budget', 'Security & InfoSec', 'Competitor Trap', or 'Timing & Priority'"
    )
    objection_quote: str = Field(
        description="Realistic buyer quote expressing the objection"
    )
    buyer_persona: str = Field(
        description="Target buyer stakeholder, e.g. 'VP of Sales Operations', 'CISO', 'CFO'"
    )
    winning_response: str = Field(
        description="Actionable executive counter-talk-track with value pivot"
    )
    proof_points: List[str] = Field(
        default_factory=list,
        description="Tangible data points or customer evidence supporting the pivot",
    )
    key_metric: str = Field(
        default="",
        description="Key financial or operational metric, e.g. '$80k net savings' or '60-day break-even'",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Short categorization pills, e.g. ['TCO Comparison', '2 FTE Savings']",
    )


class ObjectionBattlecardsDeck(BaseModel):
    account_name: str = Field(description="Name of the enterprise prospect account")
    deal_size: str = Field(default="", description="Deal size, e.g. '$150,000 ARR'")
    competitor: str = Field(default="", description="Incumbent or competing vendor")
    cards: List[ObjectionCard] = Field(
        default_factory=list, description="List of generated objection cards"
    )


class CreateBattlecardsRequest(BaseModel):
    account_name: str
    notes: str
    competitor: Optional[str] = ""
    deal_size: Optional[str] = ""


class ArtifactEnvelope(BaseModel):
    id: str
    type: str = "battlecards"
    title: str
    deal_context: dict
    created_at: str
    updated_at: str
    is_published: bool = False
    share_id: Optional[str] = None
    content: dict
