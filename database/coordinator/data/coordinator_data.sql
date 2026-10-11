-- Coordinator demo data for the distributed library coursework.
-- Campus and site boundaries come from user-collected Google Earth polygons.
-- Addresses, contact details, catalog metadata, and some point locations remain demo data.

INSERT INTO site_node (
    site_id, site_name, service_url, database_host, database_port,
    database_name, region_name, region_geometry, site_status, last_heartbeat
)
VALUES
    (
        1, 'Site 1 西北片区节点', 'http://site1-api:8000', 'site1-db', 5432,
        'site1_db', '成都西北片区',
        ST_GeomFromText(
            'MULTIPOLYGON(((103.6568073129037 30.76110776367014,103.7649061451881 30.56786511499864,104.2322956154466 30.86418215272641,104.0548526610924 30.92688681033099,103.821541815855 30.82770917761293,103.6568073129037 30.76110776367014)))',
            4326
        ),
        'ONLINE', CURRENT_TIMESTAMP
    ),
    (
        2, 'Site 2 中东片区节点', 'http://site2-api:8000', 'site2-db', 5432,
        'site2_db', '成都中东片区',
        ST_GeomFromText(
            'MULTIPOLYGON(((103.9238361238472 30.66748452070667,104.0768007879622 30.64833591159371,104.238275113661 30.60608656555041,104.2344145168687 30.86448368966519,103.9238361238472 30.66748452070667)))',
            4326
        ),
        'ONLINE', CURRENT_TIMESTAMP
    ),
    (
        3, 'Site 3 中南片区节点', 'http://site3-api:8000', 'site3-db', 5432,
        'site3_db', '成都中南片区',
        ST_GeomFromText(
            'MULTIPOLYGON(((103.7653469532362 30.56668776979852,104.0670743585507 30.43492724307242,104.2356784029659 30.60603011941879,104.0759335725686 30.64751977737894,103.9251953300807 30.66688156732137,103.7653469532362 30.56668776979852)))',
            4326
        ),
        'ONLINE', CURRENT_TIMESTAMP
    )
ON CONFLICT (site_id) DO UPDATE SET
    site_name = EXCLUDED.site_name,
    service_url = EXCLUDED.service_url,
    database_host = EXCLUDED.database_host,
    database_port = EXCLUDED.database_port,
    database_name = EXCLUDED.database_name,
    region_name = EXCLUDED.region_name,
    region_geometry = EXCLUDED.region_geometry,
    site_status = EXCLUDED.site_status,
    last_heartbeat = EXCLUDED.last_heartbeat,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO university (
    university_id, university_name, short_name, address, website, phone, status
)
VALUES
    (101, '四川大学', '川大', '成都市一环路南一段24号（模拟）', 'https://www.scu.edu.cn', '028-00000101', 'ACTIVE'),
    (102, '电子科技大学', '电子科大', '成都市高新区西源大道（模拟）', 'https://www.uestc.edu.cn', '028-00000102', 'ACTIVE'),
    (103, '西南交通大学', '西南交大', '成都市郫都区犀安路（模拟）', 'https://www.swjtu.edu.cn', '028-00000103', 'ACTIVE'),
    (104, '西南财经大学', '西南财大', '成都市温江区柳台大道（模拟）', 'https://www.swufe.edu.cn', '028-00000104', 'ACTIVE')
ON CONFLICT (university_id) DO UPDATE SET
    university_name = EXCLUDED.university_name,
    short_name = EXCLUDED.short_name,
    address = EXCLUDED.address,
    website = EXCLUDED.website,
    phone = EXCLUDED.phone,
    status = EXCLUDED.status,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO campus (
    campus_id, university_id, campus_name, address,
    longitude, latitude, center_location, boundary, site_id, status
)
VALUES
    (1001, 101, '望江校区', '成都市武侯区一环路南一段（模拟）',
        104.0831000, 30.6306000,
        ST_SetSRID(ST_MakePoint(104.0831000, 30.6306000), 4326)::geography,
        ST_GeomFromText('POLYGON((104.0765785072187 30.63012672257379,104.0790014573687 30.62905059302852,104.08255311071 30.62729487129168,104.0843506358639 30.6291554324978,104.0873470877933 30.62957471258228,104.0898400400277 30.63520661618893,104.0825264055082 30.64039343815347,104.07414070459 30.63639041803419,104.0765785072187 30.63012672257379))', 4326),
        3, 'ACTIVE'),
    (1002, 101, '华西校区', '成都市武侯区人民南路三段（模拟）',
        104.0648000, 30.6413000,
        ST_SetSRID(ST_MakePoint(104.0648000, 30.6413000), 4326)::geography,
        ST_GeomFromText('POLYGON((104.0640537238169 30.63991126618595,104.0705881221807 30.63941318684553,104.0707732073461 30.64128312504667,104.0707719430889 30.64512712884726,104.0641182641345 30.64531962578545,104.0640537238169 30.63991126618595))', 4326),
        3, 'ACTIVE'),
    (1003, 101, '江安校区', '成都市双流区川大路（模拟）',
        103.9976000, 30.5578000,
        ST_SetSRID(ST_MakePoint(103.9976000, 30.5578000), 4326)::geography,
        ST_GeomFromText('POLYGON((103.9882829989127 30.55311470814437,104.0026547157687 30.55631904672859,104.0083179051255 30.56011992911494,104.0012737191668 30.56765965121058,103.9862787059654 30.56451349474042,103.9882829989127 30.55311470814437))', 4326),
        3, 'ACTIVE'),
    (1004, 102, '清水河校区', '成都市高新区西源大道（模拟）',
        103.9275000, 30.7538000,
        ST_SetSRID(ST_MakePoint(103.9275000, 30.7538000), 4326)::geography,
        ST_GeomFromText('POLYGON((103.9329699533284 30.74266516563453,103.9384967167298 30.75477874018518,103.9285645688733 30.76257007642053,103.9220959278324 30.74721154033502,103.9329699533284 30.74266516563453))', 4326),
        1, 'ACTIVE'),
    (1005, 102, '沙河校区', '成都市成华区建设北路二段（模拟）',
        104.0975400, 30.6780569,
        ST_SetSRID(ST_MakePoint(104.0975400, 30.6780569), 4326)::geography,
        ST_GeomFromText('POLYGON((104.0958484876229 30.67484259713933,104.1018320391283 30.67663571670025,104.1005771384053 30.67924818541587,104.0980885498162 30.68033471941432,104.0961087644987 30.68133022533038,104.0946076577964 30.68089246720697,104.0941775922284 30.6791358899312,104.0951112613764 30.67801080028259,104.0944719191562 30.67753230428193,104.0958484876229 30.67484259713933))', 4326),
        2, 'ACTIVE'),
    (1006, 103, '九里校区', '成都市金牛区二环路北一段（模拟）',
        104.0522000, 30.7046000,
        ST_SetSRID(ST_MakePoint(104.0522000, 30.7046000), 4326)::geography,
        ST_GeomFromText('POLYGON((104.054959330338 30.69725810970496,104.0547694095838 30.70457349945373,104.0524577883157 30.70643541705838,104.0442060346953 30.70159411778657,104.0480468452757 30.69704949822149,104.054959330338 30.69725810970496))', 4326),
        2, 'ACTIVE'),
    (1007, 103, '犀浦校区', '成都市郫都区犀安路（模拟）',
        103.9830329, 30.7663484,
        ST_SetSRID(ST_MakePoint(103.9830329, 30.7663484), 4326)::geography,
        ST_GeomFromText('POLYGON((103.9843029071855 30.75798033672235,103.9894600102925 30.76195972331804,103.9894479199674 30.76495345546337,103.9875189077297 30.76877455586872,103.9854939412049 30.77181456002558,103.9815204883554 30.77215241421755,103.9778981443921 30.77276236744119,103.9748125972402 30.77035670511139,103.9843029071855 30.75798033672235))', 4326),
        1, 'ACTIVE'),
    (1008, 104, '柳林校区', '成都市温江区柳台大道（模拟）',
        103.8178000, 30.6815000,
        ST_SetSRID(ST_MakePoint(103.8178000, 30.6815000), 4326)::geography,
        ST_GeomFromText('POLYGON((103.8207260435865 30.67142590083381,103.8326726645923 30.67752711657402,103.8290210031152 30.68371988945163,103.8259451843348 30.68439214565317,103.8200014057441 30.69008591493465,103.8120764616893 30.68694650052123,103.8207260435865 30.67142590083381))', 4326),
        1, 'ACTIVE'),
    (1009, 104, '光华校区', '成都市青羊区光华村街（模拟）',
        104.0142000, 30.6693000,
        ST_SetSRID(ST_MakePoint(104.0142000, 30.6693000), 4326)::geography,
        ST_GeomFromText('POLYGON((104.0104982598725 30.67411108620509,104.0088715035674 30.66765083842772,104.0137885559081 30.66499769967425,104.0189929782064 30.66468978502419,104.0189197637281 30.67254562234863,104.0104982598725 30.67411108620509))', 4326),
        2, 'ACTIVE')
ON CONFLICT (campus_id) DO UPDATE SET
    university_id = EXCLUDED.university_id,
    campus_name = EXCLUDED.campus_name,
    address = EXCLUDED.address,
    longitude = EXCLUDED.longitude,
    latitude = EXCLUDED.latitude,
    center_location = EXCLUDED.center_location,
    boundary = EXCLUDED.boundary,
    site_id = EXCLUDED.site_id,
    status = EXCLUDED.status,
    updated_at = CURRENT_TIMESTAMP;

-- Root categories must be inserted before their child categories.
INSERT INTO category (
    category_id, category_name, parent_id, description, sort_order, status
)
VALUES
    (1, '计算机', NULL, '计算机科学与技术类图书', 10, 'ACTIVE'),
    (5, '文学', NULL, '中外文学作品及文学研究', 20, 'ACTIVE'),
    (6, '经济管理', NULL, '经济、金融与管理类图书', 30, 'ACTIVE'),
    (7, '数学', NULL, '数学基础及应用数学', 40, 'ACTIVE'),
    (8, '地理信息', NULL, '地理信息系统与空间数据处理', 50, 'ACTIVE')
ON CONFLICT (category_id) DO UPDATE SET
    category_name = EXCLUDED.category_name,
    parent_id = EXCLUDED.parent_id,
    description = EXCLUDED.description,
    sort_order = EXCLUDED.sort_order,
    status = EXCLUDED.status;

INSERT INTO category (
    category_id, category_name, parent_id, description, sort_order, status
)
VALUES
    (2, '数据库', 1, '数据库原理、设计与实现', 11, 'ACTIVE'),
    (3, '计算机网络', 1, '网络原理、协议与分布式通信', 12, 'ACTIVE'),
    (4, '软件工程', 1, '软件分析、设计、测试与项目管理', 13, 'ACTIVE')
ON CONFLICT (category_id) DO UPDATE SET
    category_name = EXCLUDED.category_name,
    parent_id = EXCLUDED.parent_id,
    description = EXCLUDED.description,
    sort_order = EXCLUDED.sort_order,
    status = EXCLUDED.status;

INSERT INTO book_catalog (
    book_id, isbn, title, author, translator, publisher, publish_year,
    edition, category_id, language, page_count, summary, keywords, cover_url
)
VALUES
    (10001, 'SIM-9780000000001', '数据库系统概论', '模拟作者A', NULL, '课程实验出版社', 2022, '第1版', 2, '中文', 420, '数据库基础与关系模型。', '数据库,SQL,关系模型', NULL),
    (10002, 'SIM-9780000000002', '分布式数据库原理', '模拟作者B', NULL, '课程实验出版社', 2023, '第1版', 2, '中文', 388, '分片、复制和分布式查询优化。', '分布式数据库,分片,查询优化', NULL),
    (10003, 'SIM-9780000000003', 'PostgreSQL数据库实践', '模拟作者C', NULL, '课程实验出版社', 2024, '第2版', 2, '中文', 516, 'PostgreSQL开发和管理实践。', 'PostgreSQL,SQL', NULL),
    (10004, 'SIM-9780000000004', 'SQL查询优化', '模拟作者D', NULL, '课程实验出版社', 2021, '第1版', 2, '中文', 302, 'SQL执行计划与索引设计。', 'SQL,索引,执行计划', NULL),
    (10005, 'SIM-9780000000005', '计算机网络基础', '模拟作者E', NULL, '课程实验出版社', 2020, '第3版', 3, '中文', 460, '计算机网络体系结构与协议。', '网络,TCP/IP', NULL),
    (10006, 'SIM-9780000000006', '分布式系统设计', '模拟作者F', NULL, '课程实验出版社', 2023, '第1版', 3, '中文', 440, '分布式系统模型与工程方法。', '分布式系统,一致性,通信', NULL),
    (10007, 'SIM-9780000000007', '软件工程导论', '模拟作者G', NULL, '课程实验出版社', 2021, '第2版', 4, '中文', 350, '软件生命周期与工程实践。', '软件工程,需求,测试', NULL),
    (10008, 'SIM-9780000000008', 'Python Web开发', '模拟作者H', NULL, '课程实验出版社', 2024, '第1版', 4, '中文', 398, '使用Python构建Web服务。', 'Python,FastAPI,Web', NULL),
    (10009, 'SIM-9780000000009', '数据结构与算法', '模拟作者I', NULL, '课程实验出版社', 2022, '第2版', 1, '中文', 498, '常用数据结构与算法分析。', '数据结构,算法', NULL),
    (10010, 'SIM-9780000000010', '操作系统原理', '模拟作者J', NULL, '课程实验出版社', 2020, '第3版', 1, '中文', 472, '进程、内存和文件系统原理。', '操作系统,进程,内存', NULL),
    (10011, 'SIM-9780000000011', '中国现代文学选读', '模拟作者K', NULL, '课程实验出版社', 2019, '第1版', 5, '中文', 280, '中国现代文学作品选读。', '文学,现代文学', NULL),
    (10012, 'SIM-9780000000012', '世界文学名著导读', '模拟作者L', NULL, '课程实验出版社', 2020, '第1版', 5, '中文', 310, '世界文学作品导读。', '文学,世界文学', NULL),
    (10013, 'SIM-9780000000013', '微观经济学基础', '模拟作者M', NULL, '课程实验出版社', 2022, '第2版', 6, '中文', 360, '微观经济学基础理论。', '经济学,微观经济', NULL),
    (10014, 'SIM-9780000000014', '金融数据分析', '模拟作者N', NULL, '课程实验出版社', 2024, '第1版', 6, '中文', 342, '金融数据建模与分析方法。', '金融,数据分析', NULL),
    (10015, 'SIM-9780000000015', '高等数学', '模拟作者O', NULL, '课程实验出版社', 2021, '第4版', 7, '中文', 568, '微积分与相关数学基础。', '数学,微积分', NULL),
    (10016, 'SIM-9780000000016', '线性代数', '模拟作者P', NULL, '课程实验出版社', 2020, '第3版', 7, '中文', 246, '矩阵、向量空间和线性变换。', '数学,线性代数', NULL),
    (10017, 'SIM-9780000000017', 'GIS原理与应用', '模拟作者Q', NULL, '课程实验出版社', 2023, '第2版', 8, '中文', 410, '地理信息系统基础和应用。', 'GIS,空间数据', NULL),
    (10018, 'SIM-9780000000018', 'PostGIS空间数据库', '模拟作者R', NULL, '课程实验出版社', 2024, '第1版', 8, '中文', 386, 'PostGIS空间类型、索引和查询。', 'PostGIS,GIS,空间查询', NULL),
    (10019, 'SIM-9780000000019', 'Web地图开发', '模拟作者S', NULL, '课程实验出版社', 2023, '第1版', 8, '中文', 324, 'Web地图展示与交互开发。', 'Leaflet,WebGIS,GeoJSON', NULL),
    (10020, 'SIM-9780000000020', '空间数据分析实践', '模拟作者T', NULL, '课程实验出版社', 2022, '第1版', 8, '中文', 356, '空间关系、距离和范围分析。', '空间分析,GIS', NULL)
ON CONFLICT (book_id) DO UPDATE SET
    isbn = EXCLUDED.isbn,
    title = EXCLUDED.title,
    author = EXCLUDED.author,
    translator = EXCLUDED.translator,
    publisher = EXCLUDED.publisher,
    publish_year = EXCLUDED.publish_year,
    edition = EXCLUDED.edition,
    category_id = EXCLUDED.category_id,
    language = EXCLUDED.language,
    page_count = EXCLUDED.page_count,
    summary = EXCLUDED.summary,
    keywords = EXCLUDED.keywords,
    cover_url = EXCLUDED.cover_url,
    updated_at = CURRENT_TIMESTAMP;

-- Demonstration accounts. Passwords are documented in docs/演示账号.md and
-- stored here only as PBKDF2-SHA256 hashes, never as plaintext.
INSERT INTO user_account (
    username, password_hash, display_name, role,
    reader_id, home_site_id, managed_site_id, account_status
)
VALUES
    ('admin',
        'pbkdf2_sha256$210000$admin-demo-salt$OF1qBsSxV8oMoTM1gQZvTzzY2VoKU2bQbK7PnVy98QE',
        '全局管理员', 'ADMIN', NULL, NULL, NULL, 'ACTIVE'),
    ('site1_admin',
        'pbkdf2_sha256$210000$site-demo-salt-1$hT1uq2Z3vlkQ7HxuLpkk5hJgiDnz3cfweO0nlN0RNYE',
        'Site 1 管理员', 'SITE_ADMIN', NULL, NULL, 1, 'ACTIVE'),
    ('site2_admin',
        'pbkdf2_sha256$210000$site-demo-salt-2$ShZRkwGi5GIsHRlCI7UCNgL5K-iQaxv1y97ya10OwzE',
        'Site 2 管理员', 'SITE_ADMIN', NULL, NULL, 2, 'ACTIVE'),
    ('site3_admin',
        'pbkdf2_sha256$210000$site-demo-salt-3$_E4o_k-lI3bwCAuQv_cAqeZFlYB09XMLORu9h44OJpc',
        'Site 3 管理员', 'SITE_ADMIN', NULL, NULL, 3, 'ACTIVE'),
    ('UESTC-S001',
        'pbkdf2_sha256$210000$student-demo-salt$Vh9SOj2IZ6AA43tz6O76usw_VEjtqC4BwyNb63hEF6k',
        '张晨', 'STUDENT', 110000000001, 1, NULL, 'ACTIVE'),
    ('SWJTU-S001',
        'pbkdf2_sha256$210000$student-demo-salt$Vh9SOj2IZ6AA43tz6O76usw_VEjtqC4BwyNb63hEF6k',
        '李悦', 'STUDENT', 110000000002, 1, NULL, 'ACTIVE'),
    ('SWUFE-S001',
        'pbkdf2_sha256$210000$student-demo-salt$Vh9SOj2IZ6AA43tz6O76usw_VEjtqC4BwyNb63hEF6k',
        '王帆', 'STUDENT', 110000000003, 1, NULL, 'ACTIVE'),
    ('UESTC-S002',
        'pbkdf2_sha256$210000$student-demo-salt$Vh9SOj2IZ6AA43tz6O76usw_VEjtqC4BwyNb63hEF6k',
        '陈航', 'STUDENT', 210000000002, 2, NULL, 'ACTIVE'),
    ('SWUFE-GH-S001',
        'pbkdf2_sha256$210000$student-demo-salt$Vh9SOj2IZ6AA43tz6O76usw_VEjtqC4BwyNb63hEF6k',
        '光华测试读者', 'STUDENT', 210000000004, 2, NULL, 'ACTIVE'),
    ('SCU-M001',
        'pbkdf2_sha256$210000$student-demo-salt$Vh9SOj2IZ6AA43tz6O76usw_VEjtqC4BwyNb63hEF6k',
        '周琳', 'STUDENT', 310000000001, 3, NULL, 'ACTIVE'),
    ('SCU-S002',
        'pbkdf2_sha256$210000$student-demo-salt$Vh9SOj2IZ6AA43tz6O76usw_VEjtqC4BwyNb63hEF6k',
        '孙博', 'STUDENT', 310000000002, 3, NULL, 'ACTIVE'),
    ('SCU-S003',
        'pbkdf2_sha256$210000$student-demo-salt$Vh9SOj2IZ6AA43tz6O76usw_VEjtqC4BwyNb63hEF6k',
        '吴桐', 'STUDENT', 310000000003, 3, NULL, 'ACTIVE'),
    ('SCU-S001',
        'pbkdf2_sha256$210000$student-demo-salt$Vh9SOj2IZ6AA43tz6O76usw_VEjtqC4BwyNb63hEF6k',
        '赵宁', 'STUDENT', 310000000004, 3, NULL, 'ACTIVE')
ON CONFLICT (username) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    display_name = EXCLUDED.display_name,
    role = EXCLUDED.role,
    reader_id = EXCLUDED.reader_id,
    home_site_id = EXCLUDED.home_site_id,
    managed_site_id = EXCLUDED.managed_site_id,
    account_status = EXCLUDED.account_status,
    updated_at = CURRENT_TIMESTAMP;
