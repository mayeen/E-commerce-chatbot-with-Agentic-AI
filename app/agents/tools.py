from langchain_core.tools import tool
import httpx

FAKESTORE_BASE = "https://fakestoreapi.com"

@tool
def product_search(query: str) -> dict:
    """Search products by keyword using FakestoreAPI. Returns a small list."""
    url = f"{FAKESTORE_BASE}/products"
    with httpx.Client(timeout=10.0) as client:
        r = client.get(url)
        r.raise_for_status()
        items = r.json()
    q = query.lower()
    hits = [
        {"id": it["id"], "title": it["title"], "price": it["price"], "category": it["category"]}
        for it in items if q in it["title"].lower()
    ][:5]
    return {"query": query, "results": hits}

@tool
def order_lookup(order_id: int) -> dict:
    """Lookup a demo 'order' via Fakestore carts endpoint. Returns cart info."""
    url = f"{FAKESTORE_BASE}/carts/{order_id}"
    with httpx.Client(timeout=10.0) as client:
        r = client.get(url)
        if r.status_code == 404:
            return {"order_id": order_id, "found": False}
        r.raise_for_status()
        cart = r.json()
    return {"order_id": order_id, "found": True, "cart": cart}