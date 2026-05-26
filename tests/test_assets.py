"""固定资产管理 API 测试"""
import pytest


class TestAssetLifecycle:
    """固定资产完整生命周期"""

    @pytest.fixture(autouse=True)
    def setup_data(self, client, admin_headers):
        """准备数据：部门 + 固定资产物品 + 采购入库"""
        resp = client.post("/api/v1/departments/", params={"name": "技术部"}, headers=admin_headers)
        self.dept_id = resp.json()["id"]

        resp = client.post("/api/v1/suppliers/", params={"name": "供应商"}, headers=admin_headers)
        self.supplier_id = resp.json()["id"]

        resp = client.post("/api/v1/items/", json={
            "name": "ThinkPad X1", "item_type": "fixed_asset",
            "abbreviation": "TPX1", "total_quantity": 0, "value": 9000,
        }, headers=admin_headers)
        resp = client.get("/api/v1/items/", params={"item_type": "fixed_asset"}, headers=admin_headers)
        self.item_id = resp.json()["items"][0]["id"]

        # 采购入库生成资产实例
        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": self.supplier_id, "warehouse_id": 1,
            "purchase_date": "2026-05-25",
            "items": [{"item_id": self.item_id, "quantity": 3, "unit_price": 9000, "batch_no": "B001"}],
        }, headers=admin_headers)
        resp = client.get("/api/v1/purchase-orders/", headers=admin_headers)
        client.put(f"/api/v1/purchase-orders/{resp.json()['orders'][0]['id']}/approve", headers=admin_headers)

        resp = client.get("/api/v1/assets/", params={"page_size": 10}, headers=admin_headers)
        self.asset1_id = resp.json()["assets"][0]["id"]
        self.asset2_id = resp.json()["assets"][1]["id"]
        self.asset3_id = resp.json()["assets"][2]["id"]

    def test_list_assets(self, client, admin_headers):
        """资产列表"""
        resp = client.get("/api/v1/assets/", params={"page_size": 10}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 3

    def test_filter_by_status(self, client, admin_headers):
        """按状态筛选"""
        resp = client.get("/api/v1/assets/", params={"status": "在库"}, headers=admin_headers)
        assert resp.json()["total"] == 3

    def test_assign_asset(self, client, admin_headers):
        """领用资产 → 状态变为使用中"""
        resp = client.post(
            f"/api/v1/assets/{self.asset1_id}/assign",
            params={"assigned_to_user_id": 3, "assigned_to_department_id": self.dept_id},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert "领用成功" in resp.json()["message"]

        resp = client.get(f"/api/v1/assets/{self.asset1_id}", headers=admin_headers)
        assert resp.json()["status"] == "使用中"
        assert resp.json()["current_user_id"] == 3

    def test_return_asset(self, client, admin_headers):
        """交回资产 → 状态变为在库"""
        # 先领用
        client.post(
            f"/api/v1/assets/{self.asset1_id}/assign",
            params={"assigned_to_user_id": 3, "assigned_to_department_id": self.dept_id},
            headers=admin_headers,
        )
        # 交回
        resp = client.post(
            f"/api/v1/assets/{self.asset1_id}/return",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert "已交回" in resp.json()["message"]

        resp = client.get(f"/api/v1/assets/{self.asset1_id}", headers=admin_headers)
        assert resp.json()["status"] == "在库"

    def test_transfer_asset(self, client, admin_headers):
        """转移资产 → 使用人变更"""
        # 先领用
        client.post(
            f"/api/v1/assets/{self.asset1_id}/assign",
            params={"assigned_to_user_id": 3, "assigned_to_department_id": self.dept_id},
            headers=admin_headers,
        )
        # 转移
        resp = client.post(
            f"/api/v1/assets/{self.asset1_id}/transfer",
            params={"new_user_id": 2, "new_department_id": self.dept_id},
            headers=admin_headers,
        )
        assert resp.status_code == 200

        resp = client.get(f"/api/v1/assets/{self.asset1_id}", headers=admin_headers)
        assert resp.json()["current_user_id"] == 2

    def test_repair_cycle(self, client, admin_headers):
        """送修 → 修复完成"""
        resp = client.post(
            f"/api/v1/assets/{self.asset2_id}/repair",
            params={"notes": "屏幕故障"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

        resp = client.get(f"/api/v1/assets/{self.asset2_id}", headers=admin_headers)
        assert resp.json()["status"] == "维修中"

        resp = client.post(f"/api/v1/assets/{self.asset2_id}/repair-done", headers=admin_headers)
        assert resp.status_code == 200

        resp = client.get(f"/api/v1/assets/{self.asset2_id}", headers=admin_headers)
        assert resp.json()["status"] == "在库"

    def test_update_asset_code(self, client, admin_headers):
        """手动编辑资产编号"""
        resp = client.put(
            f"/api/v1/assets/{self.asset1_id}",
            params={"asset_code": "CUSTOM-CODE-001", "serial_number": "SN123456"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_check_code_exists(self, client, admin_headers):
        """检查资产编号"""
        # 已知存在的编号
        code = resp = client.get("/api/v1/assets/", params={"page_size": 1}, headers=admin_headers)
        existing_code = code.json()["assets"][0]["asset_code"]

        resp = client.get("/api/v1/assets/check-code", params={"code": existing_code}, headers=admin_headers)
        assert resp.json()["exists"] is True

        resp = client.get("/api/v1/assets/check-code", params={"code": "NONEXISTENT-9999"}, headers=admin_headers)
        assert resp.json()["exists"] is False

    def test_asset_ledger(self, client, admin_headers):
        """资产台账"""
        resp = client.get("/api/v1/assets/ledger", params={"item_type": "fixed_asset"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 3

    def test_get_asset_detail_with_history(self, client, admin_headers):
        """资产详情含领用历史"""
        client.post(
            f"/api/v1/assets/{self.asset1_id}/assign",
            params={"assigned_to_user_id": 3, "assigned_to_department_id": self.dept_id},
            headers=admin_headers,
        )
        resp = client.get(f"/api/v1/assets/{self.asset1_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()["assignments"]) >= 1

    def test_cannot_assign_non_warehouse(self, client, admin_headers):
        """不能领用非在库资产"""
        client.post(
            f"/api/v1/assets/{self.asset1_id}/assign",
            params={"assigned_to_user_id": 3, "assigned_to_department_id": self.dept_id},
            headers=admin_headers,
        )
        # 再次领用同一资产应失败
        resp = client.post(
            f"/api/v1/assets/{self.asset1_id}/assign",
            params={"assigned_to_user_id": 2, "assigned_to_department_id": self.dept_id},
            headers=admin_headers,
        )
        assert resp.status_code == 400


class TestAssetDisposal:
    """资产报废流程"""

    @pytest.fixture(autouse=True)
    def setup_asset(self, client, admin_headers):
        """准备一个资产实例"""
        client.post("/api/v1/suppliers/", params={"name": "供应商"}, headers=admin_headers)
        client.post("/api/v1/departments/", params={"name": "技术部"}, headers=admin_headers)
        resp = client.post("/api/v1/items/", json={
            "name": "待报废资产", "item_type": "fixed_asset",
            "total_quantity": 0, "value": 5000,
        }, headers=admin_headers)
        resp = client.get("/api/v1/items/", params={"item_type": "fixed_asset"}, headers=admin_headers)
        item_id = resp.json()["items"][0]["id"]

        resp = client.get("/api/v1/suppliers/", headers=admin_headers)
        sid = resp.json()["suppliers"][0]["id"]

        resp = client.post("/api/v1/purchase-orders/", json={
            "supplier_id": sid, "warehouse_id": 1, "purchase_date": "2026-05-25",
            "items": [{"item_id": item_id, "quantity": 1, "unit_price": 5000}],
        }, headers=admin_headers)
        resp = client.get("/api/v1/purchase-orders/", headers=admin_headers)
        client.put(f"/api/v1/purchase-orders/{resp.json()['orders'][0]['id']}/approve", headers=admin_headers)

        resp = client.get("/api/v1/assets/", params={"page_size": 1}, headers=admin_headers)
        self.asset_id = resp.json()["assets"][0]["id"]

    def test_create_disposal(self, client, admin_headers):
        """创建报废申请"""
        resp = client.post("/api/v1/asset-disposals/", params={
            "asset_instance_id": self.asset_id, "disposal_type": "报废",
            "reason": "已过保修期",
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert "已提交" in resp.json()["message"]

    def test_approve_disposal(self, client, admin_headers):
        """审核通过报废 → 资产状态变为已报废"""
        resp = client.post("/api/v1/asset-disposals/", params={
            "asset_instance_id": self.asset_id, "disposal_type": "报废",
            "reason": "物理损坏",
        }, headers=admin_headers)
        resp = client.get("/api/v1/asset-disposals/", headers=admin_headers)
        disp_id = resp.json()["disposals"][0]["id"]

        resp = client.put(f"/api/v1/asset-disposals/{disp_id}/approve", headers=admin_headers)
        assert resp.status_code == 200

        resp = client.get(f"/api/v1/assets/{self.asset_id}", headers=admin_headers)
        assert resp.json()["status"] == "已报废"
