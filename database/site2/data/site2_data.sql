-- Site 2 demo fragment: campuses 1005, 1006, and 1009.
-- IDs start with 2 so the coordinator can route directly to Site 2.

-- Remove legacy Wangjiang rows after campus 1001 moved to Site 3.
DELETE FROM borrow_record_fragment WHERE borrow_id = 230000000001;
DELETE FROM reader_fragment WHERE reader_id = 210000000001;
DELETE FROM book_copy_fragment
WHERE copy_id IN (220000000001, 220000000002, 220000000003);
DELETE FROM library_fragment WHERE library_id = 200000000001;

INSERT INTO library_fragment (
    library_id, university_id, campus_id, library_name, address,
    longitude, latitude, location, open_time, close_time, phone,
    total_seats, status
)
VALUES
    (200000000002, 102, 1005, '电子科技大学沙河校区图书馆', '沙河校区内（模拟）',
        104.0975400, 30.6780569,
        ST_SetSRID(ST_MakePoint(104.0975400, 30.6780569), 4326)::geography,
        '08:00', '22:00', '028-20000002', 1200, 'OPEN'),
    (200000000003, 103, 1006, '西南交通大学九里校区图书馆', '九里校区内（模拟）',
        104.0527000, 30.7050000,
        ST_SetSRID(ST_MakePoint(104.0527000, 30.7050000), 4326)::geography,
        '08:30', '22:00', '028-20000003', 1300, 'OPEN'),
    (200000000004, 104, 1009, '西南财经大学光华校区图书馆', '光华校区内（模拟）',
        104.0142000, 30.6693000,
        ST_SetSRID(ST_MakePoint(104.0142000, 30.6693000), 4326)::geography,
        '08:30', '22:00', '028-20000004', 1000, 'OPEN')
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
    (210000000002, 102, 1005, 'UESTC-S002', 'NET-20000002', '陈航', '13800002002', 'chenhang@example.test', 'demo_hash_change_me', 'UNDERGRADUATE', TRUE, 10, 1, 'ACTIVE'),
    (210000000003, 103, 1006, 'SWJTU-T001', 'NET-20000003', '刘老师', '13800002003', 'liuteacher@example.test', 'demo_hash_change_me', 'TEACHER', TRUE, 20, 0, 'ACTIVE'),
    (210000000004, 104, 1009, 'SWUFE-GH-S001', 'NET-20000004', '光华测试读者', '13800002004', 'guanghua.reader@example.test', 'demo_hash_change_me', 'UNDERGRADUATE', TRUE, 10, 0, 'ACTIVE')
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
    (220000000004, 10005, 102, 1005, 200000000002, 200000000002, 'S2-UESTC-0001', 'N-01-01', 'BORROWED', TRUE, '2024-09-01', 62.00),
    (220000000005, 10008, 102, 1005, 200000000002, 200000000002, 'S2-UESTC-0002', 'S-02-01', 'AVAILABLE', TRUE, '2025-02-18', 70.00),
    (220000000006, 10018, 102, 1005, 200000000002, 200000000002, 'S2-UESTC-0003', 'G-03-01', 'AVAILABLE', TRUE, '2025-09-10', 68.00),
    (220000000007, 10006, 103, 1006, 200000000003, 200000000003, 'S2-SWJTU-0001', 'N-02-01', 'AVAILABLE', TRUE, '2025-01-08', 79.00),
    (220000000008, 10010, 103, 1006, 200000000003, 200000000003, 'S2-SWJTU-0002', 'O-01-01', 'AVAILABLE', FALSE, '2023-09-01', 64.00),
    (220000000009, 10016, 103, 1006, 200000000003, 200000000003, 'S2-SWJTU-0003', 'M-02-01', 'AVAILABLE', TRUE, '2024-09-01', 39.00),
    (220000000010, 10013, 104, 1009, 200000000004, 200000000004, 'S2-SWUFE-GH-0001', 'E-02-01', 'AVAILABLE', TRUE, '2025-03-12', 52.00),
    (220000000011, 10014, 104, 1009, 200000000004, 200000000004, 'S2-SWUFE-GH-0002', 'E-02-02', 'AVAILABLE', TRUE, '2025-03-12', 69.00)
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
    (230000000002, 210000000002, 1005, 10005, 220000000004,
        2, 200000000002, NULL, 'LOCAL',
        '2026-09-25 15:00:00+08', '2026-10-25 23:59:59+08', NULL,
        'BORROWING', 0, 0.00),
    (230000000003, 210000000003, 1006, 10006, 220000000007,
        2, 200000000003, 200000000003, 'LOCAL',
        '2026-07-01 09:00:00+08', '2026-08-01 23:59:59+08',
        '2026-07-28 10:00:00+08', 'RETURNED', 0, 0.00)
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
