"""供应商管理 API 测试"""
import pytest


class TestSupplierCRUD:
    """供应商 CRUD 完整流程"""

    def test_create_supplier(self, client, admin_headers):
        """创建供应商"""
        resp = client.post(
            "/api/v1/suppliers/",
            params={"name": "华为技术", "contact_person": "王经理", "phone": "0755-12345678"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "创建成功" in data["message"]
        assert data["id"] > 0

    def test_list_suppliers(self, client, admin_headers):
        """供应商列表"""
        client.post("/api/v1/suppliers/", params={"name": "测试供应商-unique"}, headers=admin_headers)
        resp = client.get("/api/v1/suppliers/", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        names = [s["name"] for s in data["suppliers"]]
        assert "测试供应商-unique" in names

    def test_update_supplier(self, client, admin_headers):
        """更新供应商"""
        resp = client.post("/api/v1/suppliers/", params={"name": "原始名称"}, headers=admin_headers)
        sid = resp.json()["id"]
        resp = client.put(f"/api/v1/suppliers/{sid}", params={"name": "更新名称"}, headers=admin_headers)
        assert resp.status_code == 200
        assert "更新成功" in resp.json()["message"]

    def test_search_supplier(self, client, admin_headers):
        """供应商搜索"""
        client.post("/api/v1/suppliers/", params={"name": "华为搜索测试-ABC"}, headers=admin_headers)
        client.post("/api/v1/suppliers/", params={"name": "中兴搜索测试-XYZ"}, headers=admin_headers)
        resp = client.get("/api/v1/suppliers/", params={"keyword": "华为搜索测试"}, headers=admin_headers)
        data = resp.json()
        assert data["total"] >= 1
        names = [s["name"] for s in data["suppliers"]]
        assert "华为搜索测试-ABC" in names

    def test_delete_supplier(self, client, admin_headers):
        """删除供应商"""
        resp = client.post("/api/v1/suppliers/", params={"name": "待删除"}, headers=admin_headers)
        sid = resp.json()["id"]
        resp = client.delete(f"/api/v1/suppliers/{sid}", headers=admin_headers)
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

    def test_delete_nonexistent(self, client, admin_headers):
        """删除不存在的供应商返回404"""
        resp = client.delete("/api/v1/suppliers/99999", headers=admin_headers)
        assert resp.status_code == 404
