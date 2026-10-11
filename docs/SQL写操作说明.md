# SQL 写操作说明

全局管理员可以在 SQL 工作台提交受控的 `INSERT`、`UPDATE` 和 `DELETE`。系统不会把用户 SQL 原样发送到数据库，而是先解析为结构化命令，再复用管理端 CRUD 服务生成参数化物理 SQL并路由到目标分节点。

## 支持范围

支持逻辑表：`reader`、`book_copy`、`borrow_record`、`library`。

```sql
INSERT INTO reader (
    home_university_id, home_campus_id, student_no,
    network_card_no, reader_name, reader_type,
    network_permission, max_borrow_count, status
) VALUES (
    102, 1004, 'UESTC-S099',
    'UESTC-CARD-099', '测试学生', 'UNDERGRADUATE',
    TRUE, 10, 'ACTIVE'
);
```

```sql
UPDATE reader
SET status = 'FROZEN', max_borrow_count = 8
WHERE reader_id = 110000000001;
```

```sql
DELETE FROM reader
WHERE reader_id = 110000000001;
```

## 安全限制

- 一次只能执行一条 SQL。
- `INSERT` 必须显式列出字段，只允许单行 `VALUES`。
- `UPDATE` 的 `SET` 只允许“字段 = 常量”。
- `UPDATE` 和 `DELETE` 必须使用本表主键的单个等值条件。
- 禁止无条件更新、无条件删除、子查询、表达式赋值和批量写入。
- 禁止直接写入主键、创建时间、更新时间和当前借阅数等系统字段。
- 分片键决定目标站点；无法精确定位时拒绝写入，不会广播写操作。
- 所有值经过 Pydantic 业务校验，并作为参数传给 PostgreSQL。
- 删除仍有关联数据的记录时，数据库外键会拒绝操作。

## 跨库处理

对 `reader` 执行 `INSERT` 时，同时在主节点 `user_account` 创建以学号为用户名的账号，初始密码为 `student123`。如果主节点账号创建失败，分节点读者会被补偿删除。删除读者时也会同步删除主节点账号。

主节点和目标分节点的实时监控界面会显示命令接收、SQL 解析、站点选择、参数化 SQL 生成、远程转发和执行结果。
