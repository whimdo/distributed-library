# 蓉图云前端

成都高校分布式图书馆课程项目的 Vue 3 前端，包含：

- 系统和四节点健康总览
- 逻辑 SQL 查询、结果表格与 CSV 导出
- 查询分解、站点裁剪和物理 SQL 展示
- 主节点与三个数据节点的 WebSocket 实时事件终端
- 基于 OpenLayers 的 PostGIS 空间数据地图
- 基于读者编号路由的借阅记录查询
- 用户逻辑表数据字典

## 启动

先启动 Docker 数据库与 Python 后端，再在项目根目录运行：

```powershell
.\scripts\start-frontend.ps1
```

浏览器打开 <http://127.0.0.1:5173>。

如端口发生变化，将 `.env.example` 复制为 `.env` 后修改地址。

## 构建检查

```powershell
npm --prefix .\frontend run build
```
