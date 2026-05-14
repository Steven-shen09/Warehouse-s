/**
 * Warehouse-s 前端 JavaScript
 * 使用 Alpine.js + HTMX + Vanilla JS
 */

// ── 全局状态 ──
const AppState = {
  token: localStorage.getItem("warehouse_token") || "",
  user: JSON.parse(localStorage.getItem("warehouse_user") || "null"),
  theme: localStorage.getItem("warehouse_theme") || "light",

  get isLoggedIn() { return !!this.token; },
  get isAdmin() { return this.user?.role === "admin"; },
  get isApprover() { return this.user?.role === "approver"; },
  get isUser() { return this.user?.role === "user"; },

  setAuth(token, user) {
    this.token = token;
    this.user = user;
    localStorage.setItem("warehouse_token", token);
    localStorage.setItem("warehouse_user", JSON.stringify(user));
  },

  clearAuth() {
    this.token = "";
    this.user = null;
    localStorage.removeItem("warehouse_token");
    localStorage.removeItem("warehouse_user");
  },

  toggleTheme() {
    this.theme = this.theme === "light" ? "dark" : "light";
    localStorage.setItem("warehouse_theme", this.theme);
    document.documentElement.setAttribute("data-theme", this.theme);
  },

  init() {
    document.documentElement.setAttribute("data-theme", this.theme);
  }
};

// ── Toast 通知 ──
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container") || createToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => { toast.remove(); }, 3000);
}

function createToastContainer() {
  const container = document.createElement("div");
  container.id = "toast-container";
  container.className = "toast-container";
  document.body.appendChild(container);
  return container;
}

// ── 模态框 ──
function openModal(id) {
  document.getElementById(id).classList.add("active");
}
function closeModal(id) {
  document.getElementById(id).classList.remove("active");
}

// ── API 请求封装 ──
async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(AppState.token ? { "Authorization": `Bearer ${AppState.token}` } : {}),
    ...options.headers,
  };

  const resp = await fetch(path, { ...options, headers });
  if (resp.status === 401) {
    AppState.clearAuth();
    window.location.href = "/login";
    throw new Error("登录已过期");
  }
  return resp;
}

// ── 初始化 ──
document.addEventListener("DOMContentLoaded", () => {
  AppState.init();
});
