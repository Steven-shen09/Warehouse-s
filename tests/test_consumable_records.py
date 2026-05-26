"""消耗品领用 API 测试"""
import pytest


class TestConsumableFlow:
    """消耗品领用完整流程"""

    @pytest.fixture(autouse=True)
    def setup_data(self, client, admin_headers):
        """准备消耗品 + 采购入库"""
        resp = client.post("/api/v1/suppliers/", params={"name": "供应商"}, headers=admin_headers)
        self.supplier_id = resp.json()["id"]

        resp = client.post("/api/v1/items/", json={
            "name": "A4打印纸", "item_type": "consumable",
            "total_quantity": 0, "value": 25,
        }, headers=admin_headers)
        resp = client.get("/api/v1/items/", params={"item_type": "consumable"}, headers=admin_headers)
        self.item_id = resp.json()["items"][0]["id"]

        # 入库100件
        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": self.supplier_id, "warehouse_id": 1,
            "purchase_date": "2026-05-25",
            "items": [{"item_id": self.item_id, "quantity": 100, "unit_price": 25}],
        }, headers=admin_headers)
        resp = client.get("/api/v1/purchase-orders/", headers=admin_headers)
        client.put(f"/api/v1/purchase-orders/{resp.json()['orders'][0]['id']}/approve", headers=admin_headers)

    def test_submit_pickup(self, client, admin_headers):
        """提交消耗品领用申请"""
        resp = client.post("/api/v1/consumable-records/", params={
            "item_id": self.item_id, "quantity": 20,
            "source_warehouse_id": 1, "pickup_date": "2026-05-25",
            "reason": "办公用纸",
        }, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "已提交" in data["message"]
        assert data["document_no"].startswith("LY-")

    def test_approve_deducts_stock(self, client, admin_headers):
        """审核通过 → 库存永久扣减"""
        # 提交
        client.post("/api/v1/consumable-records/", params={
            "item_id": self.item_id, "quantity": 20,
            "source_warehouse_id": 1, "pickup_date": "2026-05-25",
        }, headers=admin_headers)

        # 获取记录ID
        resp = client.get("/api/v1/consumable-records/", params={"status": "待审核"}, headers=admin_headers)
        rec_id = resp.json()["records"][0]["id"]

        # 审核通过
        resp = client.put(f"/api/v1/consumable-records/{rec_id}/approve", headers=admin_headers)
        assert resp.status_code == 200

        # 验证库存：100 → 80
        resp = client.get(f"/api/v1/items/{self.item_id}", headers=admin_headers)
        assert resp.json()["total_quantity"] == 80

    def test_reject_does_not_deduct(self, client, admin_headers):
        """驳回 → 库存不变"""
        client.post("/api/v1/consumable-records/", params={
            "item_id": self.item_id, "quantity": 10,
            "source_warehouse_id": 1, "pickup_date": "2026-05-25",
        }, headers=admin_headers)

        resp = client.get("/api/v1/consumable-records/", params={"status": "待审核"}, headers=admin_headers)
        rec_id = resp.json()["records"][0]["id"]

        resp = client.put(
            f"/api/v1/consumable-records/{rec_id}/reject",
            params={"comment": "不批准"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

        # 库存仍为100
        resp = client.get(f"/api/v1/items/{self.item_id}", headers=admin_headers)
        assert resp.json()["total_quantity"] == 100

    def test_list_filter_by_status(self, client, admin_headers):
        """按状态筛选"""
        client.post("/api/v1/consumable-records/", params={
            "item_id": self.item_id, "quantity": 5,
            "source_warehouse_id": 1, "pickup_date": "2026-05-25",
        }, headers=admin_headers)

        resp = client.get("/api/v1/consumable-records/", params={"status": "待审核"}, headers=admin_headers)
        assert resp.json()["total"] == 1

        resp = client.get("/api/v1/consumable-records/", params={"status": "已领取"}, headers=admin_headers)
        assert resp.json()["total"] == 0

    def test_insufficient_stock_rejected(self, client, admin_headers):
        """库存不足时拒绝"""
        # 先领走100（全量）
        client.post("/api/v1/consumable-records/", params={
            "item_id": self.item_id, "quantity": 100,
            "source_warehouse_id": 1, "pickup_date": "2026-05-25",
        }, headers=admin_headers)

        # 再提交一个领用应失败
        resp = client.post("/api/v1/consumable-records/", params={
            "item_id": self.item_id, "quantity": 1,
            "source_warehouse_id": 1, "pickup_date": "2026-05-25",
        }, headers=admin_headers)
        # 第一个待审核占用库存，第二个应失败
        assert resp.status_code == 400


class TestConsumablePermissions:
    """消耗品领用权限"""

    def test_user_can_submit(self, client, user_headers, admin_headers):
        """普通用户可以提交领用"""
        # 准备数据
        resp = client.post("/api/v1/suppliers/", params={"name": "S"}, headers=admin_headers)
        sid = resp.json()["id"]
        client.post("/api/v1/items/", json={
            "name": "纸张", "item_type": "consumable", "total_quantity": 0,
        }, headers=admin_headers)
        resp = client.get("/api/v1/items/", params={"item_type": "consumable"}, headers=admin_headers)
        item_id = resp.json()["items"][0]["id"]
        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": sid, "warehouse_id": 1, "purchase_date": "2026-05-25",
            "items": [{"item_id": item_id, "quantity": 10, "unit_price": 1}],
        }, headers=admin_headers)
        resp = client.get("/api/v1/purchase-orders/", headers=admin_headers)
        client.put(f"/api/v1/purchase-orders/{resp.json()['orders'][0]['id']}/approve", headers=admin_headers)

        # 普通用户提交领用
        resp = client.post("/api/v1/consumable-records/", params={
            "item_id": item_id, "quantity": 5,
            "source_warehouse_id": 1, "pickup_date": "2026-05-25",
        }, headers=user_headers)
        assert resp.status_code == 200

    def test_user_cannot_approve(self, client, user_headers, admin_headers):
        """普通用户不能审核"""
        resp = client.put("/api/v1/consumable-records/1/approve", headers=user_headers)
        # 记录不存在或权限不足
        assert resp.status_code in (403, 404)
