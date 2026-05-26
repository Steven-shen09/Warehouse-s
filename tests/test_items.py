"""物品管理 API 测试（含新增字段）"""


class TestItemNewFields:
    """物品新增字段测试"""

    def test_create_tool_item(self, client, admin_headers):
        """创建工具类物品"""
        resp = client.post("/api/v1/items/", json={
            "name": "投影仪Pro", "category": "电子设备",
            "item_type": "tool", "abbreviation": "TYP",
            "specification": "4K激光", "brand": "Epson",
            "total_quantity": 5, "value": 15000,
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert "创建成功" in resp.json()["message"]

    def test_create_fixed_asset_item(self, client, admin_headers):
        """创建固定资产物品（初始库存可为0）"""
        # 先创建部门
        client.post("/api/v1/departments/", params={"name": "IT部"}, headers=admin_headers)
        resp = client.post("/api/v1/items/", json={
            "name": "ThinkPad X1", "category": "电子设备",
            "item_type": "fixed_asset", "abbreviation": "TPX1",
            "specification": "14寸 i7", "brand": "Lenovo",
            "total_quantity": 0, "value": 9000, "department_id": 1,
        }, headers=admin_headers)
        assert resp.status_code == 200

    def test_create_consumable_item(self, client, admin_headers):
        """创建消耗品物品"""
        resp = client.post("/api/v1/items/", json={
            "name": "A4打印纸", "category": "办公用品",
            "item_type": "consumable", "total_quantity": 0, "value": 25,
        }, headers=admin_headers)
        assert resp.status_code == 200

    def test_filter_by_item_type(self, client, admin_headers):
        """按 item_type 筛选"""
        client.post("/api/v1/items/", json={"name": "工具A-fortest", "item_type": "tool", "total_quantity": 1}, headers=admin_headers)
        client.post("/api/v1/items/", json={"name": "消耗品B-fortest", "item_type": "consumable", "total_quantity": 0}, headers=admin_headers)
        client.post("/api/v1/items/", json={"name": "资产C-fortest", "item_type": "fixed_asset", "total_quantity": 0}, headers=admin_headers)

        resp = client.get("/api/v1/items/", params={"item_type": "consumable", "keyword": "消耗品B-fortest"}, headers=admin_headers)
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "消耗品B-fortest"

    def test_default_item_type_is_tool(self, client, admin_headers):
        """默认 item_type 为 tool（向后兼容）"""
        resp = client.post("/api/v1/items/", json={
            "name": "旧物品", "total_quantity": 3,
        }, headers=admin_headers)
        assert resp.status_code == 200
        # 获取该物品
        resp = client.get("/api/v1/items/", params={"keyword": "旧物品"}, headers=admin_headers)
        items = resp.json()["items"]
        assert items[0].get("item_type", "") == "tool"

    def test_update_item_fields(self, client, admin_headers):
        """更新物品新字段"""
        client.post("/api/v1/items/", json={"name": "待更新物品-unique", "total_quantity": 1}, headers=admin_headers)
        resp = client.get("/api/v1/items/", params={"keyword": "待更新物品-unique"}, headers=admin_headers)
        items = resp.json()["items"]
        assert len(items) == 1
        item_id = items[0]["id"]

        resp = client.put(f"/api/v1/items/{item_id}", json={
            "abbreviation": "DGX", "specification": "型号123", "brand": "测试品牌",
            "item_type": "tool",
        }, headers=admin_headers)
        assert resp.status_code == 200
