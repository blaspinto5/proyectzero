import pytest

from projectzero2.spiders.n1g_spider import parse_price
from projectzero2.pipelines import NormalizeItemPipeline, ScorePipeline


def test_parse_price_formats():
    # common formats
    assert parse_price("$1.234,56") == pytest.approx(1234.56)
    assert parse_price("1,234.56") == pytest.approx(1234.56)
    assert parse_price("1.234") == pytest.approx(1234.0)
    assert parse_price(None) is None


def test_normalize_price_and_title_mapping():
    p = NormalizeItemPipeline()
    item = {"precio": "$ 1.234,56", "title": "Mi Titulo"}
    out = p.process_item(item, None)
    assert out.get("titulo") == "Mi Titulo"
    assert out.get("precio") == "1.234,56"


def test_score_pipeline_calculation():
    s = ScorePipeline()
    item = {"stock": 5, "images": ["a", "b", "c"], "description": "x" * 201, "titulo": "t"}
    out = s.process_item(item, None)
    # stock -> +5, images (3*5)=15, description >200 -> +15 => total 35
    assert out.get("score") == 35
