-- Site 1 demo fragment: campuses 1004, 1007, and 1008.
-- IDs start with 1 so the coordinator can route directly to Site 1.

INSERT INTO library_fragment (
    library_id, university_id, campus_id, library_name, address,
    longitude, latitude, location, open_time, close_time, phone,
    total_seats, status
)
VALUES
    (100000000001, 102, 1004, '电子科技大学清水河校区图书馆', '清水河校区内（模拟）',
        103.9280000, 30.7542000,
        ST_SetSRID(ST_MakePoint(103.9280000, 30.7542000), 4326)::geography,
        '08:00', '22:00', '028-10000001', 1800, 'OPEN'),
    (100000000002, 103, 1007, '西南交通大学犀浦校区图书馆', '犀浦校区内（模拟）',
        103.9830329, 30.7663484,
        ST_SetSRID(ST_MakePoint(103.9830329, 30.7663484), 4326)::geography,
        '08:00', '22:30', '028-10000002', 1600, 'OPEN'),
    (100000000003, 104, 1008, '西南财经大学柳林校区图书馆', '柳林校区内（模拟）',
        103.8183000, 30.6819000,
        ST_SetSRID(ST_MakePoint(103.8183000, 30.6819000), 4326)::geography,
        '08:30', '22:00', '028-10000003', 1400, 'OPEN')
ON CONFLICT (library_id) DO UPDATE SET
    university_id = EXCLUDED.university_id,
    campus_id = EXCLUDED.campus_id,
    library_name = EXCLUDED.library_name,
    address = EXCLUDED.address,
    longitude = EXCLUDED.longitude,
    latitude = EXCLUDED.latitude,
    location = EXCLUDED.location,
    open_time = EXCLUDED.open_time,
    close_time = EXCLUDED.close_time,
    phone = EXCLUDED.phone,
    total_seats = EXCLUDED.total_seats,
    status = EXCLUDED.status,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO reader_fragment (
    reader_id, home_university_id, home_campus_id, student_no,
    network_card_no, reader_name, phone, email, password_hash,
    reader_type, network_permission, max_borrow_count,
    current_borrow_count, status
)
VALUES
    (110000000001, 102, 1004, 'UESTC-S001', 'NET-10000001', '张晨', '13800001001', 'zhangchen@example.test', 'demo_hash_change_me', 'UNDERGRADUATE', TRUE, 10, 1, 'ACTIVE'),
    (110000000002, 103, 1007, 'SWJTU-S001', 'NET-10000002', '李悦', '13800001002', 'liyue@example.test', 'demo_hash_change_me', 'POSTGRADUATE', TRUE, 15, 1, 'ACTIVE'),
    (110000000003, 104, 1008, 'SWUFE-S001', 'NET-10000003', '王帆', '13800001003', 'wangfan@example.test', 'demo_hash_change_me', 'UNDERGRADUATE', TRUE, 10, 0, 'ACTIVE')
ON CONFLICT (reader_id) DO UPDATE SET
    home_university_id = EXCLUDED.home_university_id,
    home_campus_id = EXCLUDED.home_campus_id,
    student_no = EXCLUDED.student_no,
    network_card_no = EXCLUDED.network_card_no,
    reader_name = EXCLUDED.reader_name,
    phone = EXCLUDED.phone,
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    reader_type = EXCLUDED.reader_type,
    network_permission = EXCLUDED.network_permission,
    max_borrow_count = EXCLUDED.max_borrow_count,
    current_borrow_count = EXCLUDED.current_borrow_count,
    status = EXCLUDED.status,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO book_copy_fragment (
    copy_id, book_id, owner_university_id, owner_campus_id,
    owner_library_id, current_library_id, barcode, shelf_location,
    copy_status, allow_cross_borrow, acquisition_date, price
)
VALUES
    (120000000001, 10001, 102, 1004, 100000000001, 100000000001, 'S1-UESTC-0001', 'A-01-01', 'AVAILABLE', TRUE, '2025-03-01', 59.00),
    (120000000002, 10002, 102, 1004, 100000000001, 100000000001, 'S1-UESTC-0002', 'A-01-02', 'AVAILABLE', TRUE, '2025-03-01', 72.00),
    (120000000003, 10018, 102, 1004, 100000000001, 100000000001, 'S1-UESTC-0003', 'G-02-01', 'AVAILABLE', TRUE, '2025-09-10', 68.00),
    (120000000004, 10009, 103, 1007, 100000000002, 100000000002, 'S1-SWJTU-0001', 'B-03-01', 'BORROWED', TRUE, '2024-10-12', 66.00),
    (120000000005, 10006, 103, 1007, 100000000002, 100000000002, 'S1-SWJTU-0002', 'B-03-02', 'AVAILABLE', TRUE, '2025-01-08', 79.00),
    (120000000006, 10015, 103, 1007, 100000000002, 100000000002, 'S1-SWJTU-0003', 'M-01-01', 'AVAILABLE', FALSE, '2024-09-01', 48.00),
    (120000000007, 10013, 104, 1008, 100000000003, 100000000003, 'S1-SWUFE-0001', 'E-01-01', 'AVAILABLE', TRUE, '2025-02-15', 52.00),
    (120000000008, 10014, 104, 1008, 100000000003, 100000000003, 'S1-SWUFE-0002', 'E-01-02', 'AVAILABLE', TRUE, '2025-02-15', 69.00),
    (120000000009, 10017, 104, 1008, 100000000003, 100000000003, 'S1-SWUFE-0003', 'G-01-01', 'AVAILABLE', TRUE, '2025-08-20', 65.00)
ON CONFLICT (copy_id) DO UPDATE SET
    book_id = EXCLUDED.book_id,
    owner_university_id = EXCLUDED.owner_university_id,
    owner_campus_id = EXCLUDED.owner_campus_id,
    owner_library_id = EXCLUDED.owner_library_id,
    current_library_id = EXCLUDED.current_library_id,
    barcode = EXCLUDED.barcode,
    shelf_location = EXCLUDED.shelf_location,
    copy_status = EXCLUDED.copy_status,
    allow_cross_borrow = EXCLUDED.allow_cross_borrow,
    acquisition_date = EXCLUDED.acquisition_date,
    price = EXCLUDED.price,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO borrow_record_fragment (
    borrow_id, reader_id, reader_home_campus_id, book_id, copy_id,
    copy_owner_site_id, checkout_library_id, return_library_id,
    borrow_type, borrow_time, due_time, return_time, borrow_status,
    renew_count, fine_amount
)
VALUES
    -- Cross-university case: an UESTC reader borrows a Sichuan University copy from Site 3.
    (130000000001, 110000000001, 1004, 10001, 320000000009,
        3, 300000000003, NULL, 'CROSS_UNIVERSITY',
        '2026-10-01 10:00:00+08', '2026-10-31 23:59:59+08', NULL,
        'BORROWING', 0, 0.00),
    (130000000002, 110000000002, 1007, 10009, 120000000004,
        1, 100000000002, NULL, 'LOCAL',
        '2026-09-01 09:30:00+08', '2026-10-01 23:59:59+08', NULL,
        'OVERDUE', 1, 5.00),
    (130000000003, 110000000003, 1008, 10013, 120000000007,
        1, 100000000003, 100000000003, 'LOCAL',
        '2026-08-10 14:00:00+08', '2026-09-10 23:59:59+08',
        '2026-09-02 16:30:00+08', 'RETURNED', 0, 0.00)
ON CONFLICT (borrow_id) DO UPDATE SET
    reader_id = EXCLUDED.reader_id,
    reader_home_campus_id = EXCLUDED.reader_home_campus_id,
    book_id = EXCLUDED.book_id,
    copy_id = EXCLUDED.copy_id,
    copy_owner_site_id = EXCLUDED.copy_owner_site_id,
    checkout_library_id = EXCLUDED.checkout_library_id,
    return_library_id = EXCLUDED.return_library_id,
    borrow_type = EXCLUDED.borrow_type,
    borrow_time = EXCLUDED.borrow_time,
    due_time = EXCLUDED.due_time,
    return_time = EXCLUDED.return_time,
    borrow_status = EXCLUDED.borrow_status,
    renew_count = EXCLUDED.renew_count,
    fine_amount = EXCLUDED.fine_amount,
    updated_at = CURRENT_TIMESTAMP;
