"""采购入库 API 测试"""
import pytest


class TestPurchaseOrder:
    """采购入库完整流程"""

    @pytest.fixture(autouse=True)
    def setup_data(self, client, admin_headers):
        """准备供应商、物品数据"""
        resp = client.post("/api/v1/suppliers/", params={"name": "测试供应商"}, headers=admin_headers)
        self.supplier_id = resp.json()["id"]

        resp = client.post("/api/v1/items/", json={
            "name": "ThinkPad X1", "item_type": "fixed_asset",
            "abbreviation": "TPX1", "total_quantity": 0, "value": 9000,
        }, headers=admin_headers)
        resp = client.get("/api/v1/items/", params={"item_type": "fixed_asset"}, headers=admin_headers)
        self.fixed_item_id = resp.json()["items"][0]["id"]

        resp = client.post("/api/v1/items/", json={
            "name": "A4纸", "item_type": "consumable", "total_quantity": 0, "value": 25,
        }, headers=admin_headers)
        resp = client.get("/api/v1/items/", params={"item_type": "consumable"}, headers=admin_headers)
        self.cons_item_id = resp.json()["items"][0]["id"]

    def test_create_purchase_order(self, client, admin_headers):
        """创建采购单"""
        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": self.supplier_id, "warehouse_id": 1,
            "purchase_date": "2026-05-25",
            "items": [{"item_id": self.cons_item_id, "quantity": 50, "unit_price": 25}],
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert "创建成功" in resp.json()["message"]
        assert resp.json()["document_no"].startswith("CG-")

    def test_approve_fixed_asset_creates_instances(self, client, admin_headers):
        """审核通过固定资产采购 → 自动生成资产实例"""
        # 创建采购单
        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": self.supplier_id, "warehouse_id": 1,
            "purchase_date": "2026-05-25",
            "items": [{"item_id": self.fixed_item_id, "quantity": 3, "unit_price": 9000, "batch_no": "B001"}],
        }, headers=admin_headers)
        assert resp.status_code == 200

        # 获取采购单ID
        resp = client.get("/api/v1/purchase-orders/", headers=admin_headers)
        po_id = resp.json()["orders"][0]["id"]

        # 审核通过
        resp = client.put(f"/api/v1/purchase-orders/{po_id}/approve", headers=admin_headers)
        assert resp.status_code == 200
        assert "已入库" in resp.json()["message"]

        # 验证资产实例
        resp = client.get("/api/v1/assets/", params={"page_size": 10}, headers=admin_headers)
        data = resp.json()
        assert data["total"] == 3
        assert all("TPX1" in a["asset_code"] for a in data["assets"])

    def test_approve_updates_stock(self, client, admin_headers):
        """审核通过消耗品采购 → 更新库存"""
        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": self.supplier_id, "warehouse_id": 1,
            "purchase_date": "2026-05-25",
            "items": [{"item_id": self.cons_item_id, "quantity": 100, "unit_price": 25}],
        }, headers=admin_headers)
        resp = client.get("/api/v1/purchase-orders/", headers=admin_headers)
        po_id = resp.json()["orders"][0]["id"]

        client.put(f"/api/v1/purchase-orders/{po_id}/approve", headers=admin_headers)

        # 验证库存
        resp = client.get(f"/api/v1/items/{self.cons_item_id}", headers=admin_headers)
        assert resp.json()["total_quantity"] == 100

    def test_cancel_purchase_order(self, client, admin_headers):
        """取消采购单"""
        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": self.supplier_id, "warehouse_id": 1,
            "purchase_date": "2026-05-25",
            "items": [{"item_id": self.cons_item_id, "quantity": 1, "unit_price": 1}],
        }, headers=admin_headers)
        resp = client.get("/api/v1/purchase-orders/", headers=admin_headers)
        po_id = resp.json()["orders"][0]["id"]

        resp = client.put(f"/api/v1/purchase-orders/{po_id}/cancel", headers=admin_headers)
        assert resp.status_code == 200

        # 状态变为已取消
        resp = client.get(f"/api/v1/purchase-orders/{po_id}", headers=admin_headers)
        assert resp.json()["status"] == "已取消"

    def test_list_with_items(self, client, admin_headers):
        """采购单列表含明细"""
        client.post("/api/v1/purchase-orders/", json={
            "supplier_id": self.supplier_id, "warehouse_id": 1,
            "purchase_date": "2026-05-25",
            "items": [{"item_id": self.cons_item_id, "quantity": 10, "unit_price": 25}],
        }, headers=admin_headers)
        resp = client.get("/api/v1/purchase-orders/", headers=admin_headers)
        data = resp.json()
        assert data["total"] == 1
        assert len(data["orders"][0]["items"]) == 1
