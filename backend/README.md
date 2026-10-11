# Python 后端

## 功能

- 主节点逻辑 SQL 接口；
- SQL 解析、字段与表白名单校验；
- 逻辑表到物理表改写；
- ID 前缀和 `campus.site_id` 路由；
- 无法精确路由时并行查询三个站点；
- 结果合并、全局排序、LIMIT 和基础聚合；
- 主节点与分节点实时事件接口；
- `ADMIN` 受控执行逻辑表 `INSERT`、`UPDATE`、`DELETE`；
- 学生、站点管理员和全局管理员的登录与权限隔离；
- FastAPI Swagger 测试页面。

## 安装

全新主机建议先在项目根目录执行一键初始化：

```powershell
Copy-Item .env.example .env
.\scripts\bootstrap.ps1
```

只安装或刷新 Python 虚拟环境时运行：

```powershell
.\scripts\setup-backend.ps1
```

## 启动

先启动并初始化数据库：

```powershell
.\scripts\import-data.ps1
```

再启动四个 API：

```powershell
.\scripts\start-backend.ps1
```

地址：

| 服务           | 地址                                                     |
| -------------- | -------------------------------------------------------- |
| 主节点 Swagger | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| Site 1 Swagger | [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) |
| Site 2 Swagger | [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs) |
| Site 3 Swagger | [http://127.0.0.1:8003/docs](http://127.0.0.1:8003/docs) |

## 执行逻辑查询

打开主节点 Swagger，选择 `POST /api/query`，输入：

```json
{
  "sql": "SELECT borrow_id, reader_id, book_id, borrow_status FROM borrow_record WHERE reader_id = 110000000001"
}
```

也可以使用 PowerShell：

```powershell
$body = @{
    sql = "SELECT library_id, library_name FROM library WHERE campus_id = 1009"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri 'http://127.0.0.1:8000/api/query' `
    -ContentType 'application/json' `
    -Body $body
```

## 事件接口

```text
主节点：http://127.0.0.1:8000/api/events
Site 1：http://127.0.0.1:8001/api/events
Site 2：http://127.0.0.1:8002/api/events
Site 3：http://127.0.0.1:8003/api/events
```

WebSocket：

```text
ws://127.0.0.1:8000/ws/events
ws://127.0.0.1:8001/ws/events
ws://127.0.0.1:8002/ws/events
ws://127.0.0.1:8003/ws/events
```

## 测试

```powershell
.\scripts\test-backend.ps1
```

用户可见表和字段见 `docs/用户逻辑表结构.md`。
受控写 SQL 的范围见 `docs/SQL写操作说明.md`。
