"""权限控制测试"""


class TestRBAC:
    """RBAC 权限验证"""

    def test_user_cannot_create_supplier(self, client, user_headers):
        """普通用户不能创建供应商"""
        resp = client.post("/api/v1/suppliers/", params={"name": "XX公司"}, headers=user_headers)
        assert resp.status_code == 403

    def test_user_cannot_create_department(self, client, user_headers):
        """普通用户不能创建部门"""
        resp = client.post("/api/v1/departments/", params={"name": "XX部"}, headers=user_headers)
        assert resp.status_code == 403

    def test_approver_can_create_supplier(self, client, approver_headers):
        """审核员可以创建供应商"""
        resp = client.post("/api/v1/suppliers/", params={"name": "XX公司"}, headers=approver_headers)
        assert resp.status_code == 200

    def test_approver_cannot_create_department(self, client, approver_headers):
        """审核员不能创建部门（仅admin）"""
        resp = client.post("/api/v1/departments/", params={"name": "XX部"}, headers=approver_headers)
        assert resp.status_code == 403

    def test_approver_cannot_delete_supplier(self, client, approver_headers, admin_headers):
        """审核员不能删除供应商"""
        client.post("/api/v1/suppliers/", params={"name": "待删"}, headers=admin_headers)
        resp = client.delete("/api/v1/suppliers/1", headers=approver_headers)
        assert resp.status_code == 403

    def test_user_can_access_consumable_records(self, client, user_headers):
        """普通用户可以访问消耗品领用"""
        resp = client.get("/api/v1/consumable-records/", headers=user_headers)
        assert resp.status_code == 200
