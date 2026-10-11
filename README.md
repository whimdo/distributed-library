# 高校分布式图书馆系统

本项目使用 1 个 PostgreSQL/PostGIS 主节点、3 个 PostgreSQL/PostGIS 数据分节点、Python FastAPI 后端和 Vue 3 前端。

## 全新主机快速搭建

先安装并启动：

- Docker Desktop（使用 Linux containers）；
- Python 3.11 或更高版本；
- Node.js 20 或更高版本。

在项目根目录打开 PowerShell：

```powershell
Copy-Item .env.example .env
.\scripts\bootstrap.ps1
```

如本机端口被占用，先修改 `.env` 中的 `COORDINATOR_DB_PORT`、`SITE1_DB_PORT`、`SITE2_DB_PORT`、`SITE3_DB_PORT`，Compose 和 Python 后端会读取同一配置。

初始化完成后，打开两个 PowerShell 窗口分别执行：

```powershell
.\scripts\start-backend.ps1
```

```powershell
.\scripts\start-frontend.ps1
```

浏览器访问 [http://127.0.0.1:5173](http://127.0.0.1:5173)。

## 常用脚本

| 脚本                         | 用途                                               |
| ---------------------------- | -------------------------------------------------- |
| `scripts/bootstrap.ps1`      | 新主机一键启动数据库、导入数据、安装全部依赖并验证 |
| `scripts/import-data.ps1`    | 幂等应用扩展、数据库结构和演示数据                 |
| `scripts/verify-data.ps1`    | 检查四个数据库的核心数据量和跨校借阅样例           |
| `scripts/setup-backend.ps1`  | 创建 Python 虚拟环境并安装后端依赖                 |
| `scripts/setup-frontend.ps1` | 按锁文件安装前端依赖                               |
| `scripts/test-backend.ps1`   | 运行后端自动测试                                   |
| `scripts/start-backend.ps1`  | 启动主节点与三个分节点 API                         |
| `scripts/start-frontend.ps1` | 启动前端开发服务器                                 |

只想重建演示数据时运行：

```powershell
.\scripts\import-data.ps1
.\scripts\verify-data.ps1
```

初始化脚本不会删除 Docker 数据卷，也不会整体清空业务表。同主键演示数据会更新，种子脚本明确列出的少量已废弃演示 ID 会被移除，其他自建数据保留。Docker 数据卷不是项目文件的一部分，换机后会由 SQL 脚本重新创建结构和演示数据。

详细结构见 [数据库结构设计.md](数据库结构设计.md)，逻辑 SQL 表见 [docs/用户逻辑表结构.md](docs/用户逻辑表结构.md)。
