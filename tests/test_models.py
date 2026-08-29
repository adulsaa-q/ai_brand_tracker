from src.models.entities import BrandEntity
from src.models.observations import BrandMentionDetail, CitationSource


def test_brand_entity_creation():
    brand = BrandEntity(
        id="konvy", name="Konvy", vertical="beauty_retail", aliases=["คอนวี่", "konvy"], official_domains=["konvy.com"]
    )
    assert brand.id == "konvy"
    assert "คอนวี่" in brand.aliases
    assert brand.is_focal_brand is False


def test_brand_mention_detail_validation():
    mention = BrandMentionDetail(
        brand_id="shopee",
        brand_name="Shopee",
        mentioned=True,
        rank=1,
        recommendation_intent="strongly_recommended",
        sentiment="positive",
        key_strengths_mentioned=["ส่งฟรี", "โค้ดลดเยอะ"],
    )
    assert mention.rank == 1
    assert mention.sentiment == "positive"
    assert len(mention.key_strengths_mentioned) == 2


def test_citation_source():
    citation = CitationSource(domain="pantip.com", source_type="forum", title="กระทู้รีวิวเทียบสกินแคร์")
    assert citation.domain == "pantip.com"
    assert citation.source_type == "forum"
