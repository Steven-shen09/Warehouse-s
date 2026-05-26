"""部门管理 API 测试"""


class TestDepartmentCRUD:
    """部门 CRUD 完整流程"""

    def test_create_department(self, client, admin_headers):
        """创建部门"""
        resp = client.post(
            "/api/v1/departments/",
            params={"name": "技术部", "description": "研发团队"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "创建成功" in data["message"]
        assert data["id"] > 0

    def test_create_duplicate_name(self, client, admin_headers):
        """创建同名部门 — 唯一约束应触发错误"""
        client.post("/api/v1/departments/", params={"name": "财务部-unique"}, headers=admin_headers)
        resp = client.post("/api/v1/departments/", params={"name": "财务部-unique"}, headers=admin_headers)
        # 唯一约束冲突返回错误（500 Internal Error 或 400）
        assert resp.status_code != 200

    def test_create_child_department(self, client, admin_headers):
        """创建子部门"""
        resp = client.post("/api/v1/departments/", params={"name": "技术部"}, headers=admin_headers)
        parent_id = resp.json()["id"]
        resp = client.post(
            "/api/v1/departments/",
            params={"name": "前端组", "parent_id": parent_id},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert "创建成功" in resp.json()["message"]

    def test_tree_view(self, client, admin_headers):
        """部门树形视图"""
        resp = client.post("/api/v1/departments/", params={"name": "技术部"}, headers=admin_headers)
        pid = resp.json()["id"]
        client.post("/api/v1/departments/", params={"name": "前端组", "parent_id": pid}, headers=admin_headers)
        client.post("/api/v1/departments/", params={"name": "后端组", "parent_id": pid}, headers=admin_headers)

        resp = client.get("/api/v1/departments/tree", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["departments"]) == 1
        assert len(data["departments"][0]["children"]) == 2

    def test_list_view(self, client, admin_headers):
        """部门列表视图"""
        client.post("/api/v1/departments/", params={"name": "A部门"}, headers=admin_headers)
        client.post("/api/v1/departments/", params={"name": "B部门"}, headers=admin_headers)
        resp = client.get("/api/v1/departments/", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()["departments"]) == 2

    def test_delete_with_children_blocked(self, client, admin_headers):
        """有子部门时不允许删除"""
        resp = client.post("/api/v1/departments/", params={"name": "父部门"}, headers=admin_headers)
        pid = resp.json()["id"]
        client.post("/api/v1/departments/", params={"name": "子部门", "parent_id": pid}, headers=admin_headers)
        resp = client.delete(f"/api/v1/departments/{pid}", headers=admin_headers)
        assert resp.status_code == 400
