import os
from pathlib import Path
from parsel import Selector
import sys
from pathlib import Path

# ensure repo root is on sys.path so tests can import package
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

import importlib.util

# load spider module directly from file to avoid import path/package issues during tests
spider_path = repo_root / "projectzero2" / "spiders" / "n1g_spider.py"
spec = importlib.util.spec_from_file_location("n1g_spider", str(spider_path))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
extract_product = mod.extract_product


def test_extract_product_from_local_html():
    # locate the sample html placed by the user
    repo_root = Path(__file__).parent.parent
    html_path = repo_root / "projectzero2" / "html2222" / "OPEN BOX ASUS Prime RTX 5050 8 GB GDDR6 OC Edition lista para SFF PCIe 5.0, 8 GB GDDR6 PRIME-RTX5050-O8G.html"
    assert html_path.exists(), f"test HTML not found: {html_path}"

    text = html_path.read_text(encoding="utf-8")
    sel = Selector(text=text)
    item = extract_product(sel, base_url=f"file://{html_path.as_posix()}")

    assert item is not None
    assert "OPEN BOX ASUS Prime RTX 5050" in (item.get("titulo") or "")
    # price_content was observed as '309000' in the sample
    assert item.get("price_content") == "309000"
    assert item.get("images") and len(item["images"]) >= 1
    assert "Rendimiento de IA" in (item.get("description") or "")
