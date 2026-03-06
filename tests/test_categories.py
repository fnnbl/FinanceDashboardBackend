"""
Tests for category endpoints:
  GET    /categories/
  POST   /categories/
  PUT    /categories/{category_id}
  DELETE /categories/{category_id}
"""
import pytest
from tests.conftest import create_plan, create_budget_item, get_expense_category_id, get_income_category_id


async def create_custom_category(client, headers, name="Benutzerdefiniert", type="expense") -> dict:
    r = await client.post("/api/v1/categories/", json={"name": name, "type": type}, headers=headers)
    return r.json()


class TestListCategories:
    async def test_list_all_categories(self, client, auth_headers):
        r = await client.get("/api/v1/categories/", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_list_categories_contains_system_categories(self, client, auth_headers):
        r = await client.get("/api/v1/categories/", headers=auth_headers)
        names = [c["name"] for c in r.json()]
        assert "Gehalt" in names
        assert "Miete" in names

    async def test_list_categories_filter_expense(self, client, auth_headers):
        r = await client.get("/api/v1/categories/?type=expense", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        assert all(c["type"] == "expense" for c in data)

    async def test_list_categories_filter_income(self, client, auth_headers):
        r = await client.get("/api/v1/categories/?type=income", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        assert all(c["type"] == "income" for c in data)

    async def test_list_categories_unauthenticated(self, client):
        r = await client.get("/api/v1/categories/")
        assert r.status_code == 403

    async def test_list_categories_invalid_type_filter(self, client, auth_headers):
        r = await client.get("/api/v1/categories/?type=invalid", headers=auth_headers)
        assert r.status_code == 422


class TestCreateCategory:
    async def test_create_expense_category(self, client, auth_headers):
        r = await client.post("/api/v1/categories/", json={"name": "Haustiere", "type": "expense"}, headers=auth_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Haustiere"
        assert data["type"] == "expense"
        assert data["is_system"] is False

    async def test_create_income_category(self, client, auth_headers):
        r = await client.post("/api/v1/categories/", json={"name": "Dividenden", "type": "income"}, headers=auth_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Dividenden"
        assert data["type"] == "income"

    async def test_create_category_duplicate_name(self, client, auth_headers):
        await client.post("/api/v1/categories/", json={"name": "Duplikat", "type": "expense"}, headers=auth_headers)
        r = await client.post("/api/v1/categories/", json={"name": "Duplikat", "type": "income"}, headers=auth_headers)
        assert r.status_code == 409

    async def test_create_category_duplicate_system_name(self, client, auth_headers):
        r = await client.post("/api/v1/categories/", json={"name": "Miete", "type": "expense"}, headers=auth_headers)
        assert r.status_code == 409

    async def test_create_category_missing_name(self, client, auth_headers):
        r = await client.post("/api/v1/categories/", json={"type": "expense"}, headers=auth_headers)
        assert r.status_code == 422

    async def test_create_category_missing_type(self, client, auth_headers):
        r = await client.post("/api/v1/categories/", json={"name": "OhneTyp"}, headers=auth_headers)
        assert r.status_code == 422

    async def test_create_category_invalid_type(self, client, auth_headers):
        r = await client.post("/api/v1/categories/", json={"name": "Test", "type": "savings"}, headers=auth_headers)
        assert r.status_code == 422

    async def test_create_category_empty_name(self, client, auth_headers):
        r = await client.post("/api/v1/categories/", json={"name": "", "type": "expense"}, headers=auth_headers)
        assert r.status_code == 422

    async def test_create_category_unauthenticated(self, client):
        r = await client.post("/api/v1/categories/", json={"name": "Test", "type": "expense"})
        assert r.status_code == 403

    async def test_created_category_appears_in_list(self, client, auth_headers):
        await client.post("/api/v1/categories/", json={"name": "Neuanlage", "type": "expense"}, headers=auth_headers)
        r = await client.get("/api/v1/categories/", headers=auth_headers)
        names = [c["name"] for c in r.json()]
        assert "Neuanlage" in names


class TestUpdateCategory:
    async def test_update_category_name(self, client, auth_headers):
        cat = await create_custom_category(client, auth_headers, name="Alter Name")
        r = await client.put(f"/api/v1/categories/{cat['id']}", json={"name": "Neuer Name"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Neuer Name"

    async def test_update_category_same_name(self, client, auth_headers):
        cat = await create_custom_category(client, auth_headers, name="Unveraendert")
        r = await client.put(f"/api/v1/categories/{cat['id']}", json={"name": "Unveraendert"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Unveraendert"

    async def test_update_category_name_conflict(self, client, auth_headers):
        await create_custom_category(client, auth_headers, name="Bereits vorhanden")
        cat = await create_custom_category(client, auth_headers, name="Wird umbenannt")
        r = await client.put(f"/api/v1/categories/{cat['id']}", json={"name": "Bereits vorhanden"}, headers=auth_headers)
        assert r.status_code == 409

    async def test_update_system_category_name_conflict(self, client, auth_headers):
        cat = await create_custom_category(client, auth_headers, name="Meine Kategorie")
        r = await client.put(f"/api/v1/categories/{cat['id']}", json={"name": "Miete"}, headers=auth_headers)
        assert r.status_code == 409

    async def test_update_category_not_found(self, client, auth_headers):
        r = await client.put("/api/v1/categories/99999", json={"name": "X"}, headers=auth_headers)
        assert r.status_code == 404

    async def test_update_category_missing_name(self, client, auth_headers):
        cat = await create_custom_category(client, auth_headers)
        r = await client.put(f"/api/v1/categories/{cat['id']}", json={}, headers=auth_headers)
        assert r.status_code == 422

    async def test_update_category_unauthenticated(self, client, auth_headers):
        cat = await create_custom_category(client, auth_headers)
        r = await client.put(f"/api/v1/categories/{cat['id']}", json={"name": "X"})
        assert r.status_code == 403


class TestDeleteCategory:
    async def test_delete_custom_category_success(self, client, auth_headers):
        cat = await create_custom_category(client, auth_headers, name="ZumLoeschen")
        r = await client.delete(f"/api/v1/categories/{cat['id']}", headers=auth_headers)
        assert r.status_code == 204

    async def test_delete_category_no_longer_in_list(self, client, auth_headers):
        cat = await create_custom_category(client, auth_headers, name="Verschwindet")
        await client.delete(f"/api/v1/categories/{cat['id']}", headers=auth_headers)
        r = await client.get("/api/v1/categories/", headers=auth_headers)
        names = [c["name"] for c in r.json()]
        assert "Verschwindet" not in names

    async def test_delete_system_category_forbidden(self, client, auth_headers):
        expense_cat_id = await get_expense_category_id(client, auth_headers)
        r = await client.delete(f"/api/v1/categories/{expense_cat_id}", headers=auth_headers)
        assert r.status_code == 403

    async def test_delete_category_with_items_no_reassign(self, client, auth_headers):
        cat = await create_custom_category(client, auth_headers, name="MitPosten")
        plan = await create_plan(client, auth_headers)
        await create_budget_item(client, auth_headers, plan["id"], category_id=cat["id"])

        r = await client.delete(f"/api/v1/categories/{cat['id']}", headers=auth_headers)
        assert r.status_code == 409

    async def test_delete_category_with_items_and_reassign(self, client, auth_headers):
        cat = await create_custom_category(client, auth_headers, name="AltKategorie")
        new_cat = await create_custom_category(client, auth_headers, name="NeuKategorie")
        plan = await create_plan(client, auth_headers)
        item_r = await create_budget_item(client, auth_headers, plan["id"], category_id=cat["id"])
        item = item_r.json()

        r = await client.delete(
            f"/api/v1/categories/{cat['id']}?reassign_to={new_cat['id']}",
            headers=auth_headers,
        )
        assert r.status_code == 204

        r = await client.get(f"/api/v1/plans/{plan['id']}/items/", headers=auth_headers)
        items = r.json()
        assert any(i["id"] == item["id"] and i["category_id"] == new_cat["id"] for i in items)

    async def test_delete_category_reassign_target_not_found(self, client, auth_headers):
        cat = await create_custom_category(client, auth_headers, name="OhneZiel")
        plan = await create_plan(client, auth_headers)
        await create_budget_item(client, auth_headers, plan["id"], category_id=cat["id"])

        r = await client.delete(
            f"/api/v1/categories/{cat['id']}?reassign_to=99999",
            headers=auth_headers,
        )
        assert r.status_code == 404

    async def test_delete_category_not_found(self, client, auth_headers):
        r = await client.delete("/api/v1/categories/99999", headers=auth_headers)
        assert r.status_code == 404

    async def test_delete_category_unauthenticated(self, client, auth_headers):
        cat = await create_custom_category(client, auth_headers)
        r = await client.delete(f"/api/v1/categories/{cat['id']}")
        assert r.status_code == 403
