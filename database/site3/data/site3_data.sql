-- Site 3 demo fragment: campuses 1001, 1002, and 1003.
-- IDs start with 3 so the coordinator can route directly to Site 3.

INSERT INTO library_fragment (
    library_id, university_id, campus_id, library_name, address,
    longitude, latitude, location, open_time, close_time, phone,
    total_seats, status
)
VALUES
    (300000000001, 101, 1002, '四川大学华西校区图书馆', '华西校区内（模拟）',
        104.0652000, 30.6417000,
        ST_SetSRID(ST_MakePoint(104.0652000, 30.6417000), 4326)::geography,
        '08:00', '22:00', '028-30000001', 1100, 'OPEN'),
    (300000000002, 101, 1003, '四川大学江安校区图书馆', '江安校区内（模拟）',
        103.9981000, 30.5582000,
        ST_SetSRID(ST_MakePoint(103.9981000, 30.5582000), 4326)::geography,
        '08:00', '22:30', '028-30000002', 2000, 'OPEN'),
    (300000000003, 101, 1001, '四川大学望江校区图书馆', '望江校区内（模拟）',
        104.0831000, 30.6306000,
        ST_SetSRID(ST_MakePoint(104.0831000, 30.6306000), 4326)::geography,
        '08:00', '22:30', '028-30000003', 2200, 'OPEN')
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
    (310000000001, 101, 1002, 'SCU-M001', 'NET-30000001', '周琳', '13800003001', 'zhoulin@example.test', 'demo_hash_change_me', 'POSTGRADUATE', TRUE, 15, 1, 'ACTIVE'),
    (310000000002, 101, 1003, 'SCU-S002', 'NET-30000002', '孙博', '13800003002', 'sunbo@example.test', 'demo_hash_change_me', 'UNDERGRADUATE', TRUE, 10, 0, 'ACTIVE'),
    (310000000003, 101, 1003, 'SCU-S003', 'NET-30000003', '吴桐', '13800003003', 'wutong@example.test', 'demo_hash_change_me', 'UNDERGRADUATE', FALSE, 8, 0, 'ACTIVE'),
    (310000000004, 101, 1001, 'SCU-S001', 'NET-30000004', '赵宁', '13800003004', 'zhaoning@example.test', 'demo_hash_change_me', 'POSTGRADUATE', TRUE, 15, 1, 'ACTIVE')
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
    -- This copy is borrowed by reader 310000000004 from Wangjiang campus.
    (320000000001, 10017, 101, 1003, 300000000002, 300000000002, 'S3-SCU-JA-0001', 'G-01-01', 'BORROWED', TRUE, '2025-01-08', 65.00),
    (320000000002, 10018, 101, 1003, 300000000002, 300000000002, 'S3-SCU-JA-0002', 'G-01-02', 'AVAILABLE', TRUE, '2025-09-10', 68.00),
    (320000000003, 10003, 101, 1002, 300000000001, 300000000001, 'S3-SCU-HX-0001', 'A-01-01', 'BORROWED', TRUE, '2025-05-12', 76.00),
    (320000000004, 10015, 101, 1002, 300000000001, 300000000001, 'S3-SCU-HX-0002', 'M-01-01', 'AVAILABLE', FALSE, '2024-09-01', 48.00),
    (320000000005, 10012, 101, 1002, 300000000001, 300000000001, 'S3-SCU-HX-0003', 'L-02-01', 'AVAILABLE', TRUE, '2024-02-20', 45.00),
    (320000000006, 10011, 101, 1003, 300000000002, 300000000002, 'S3-SCU-JA-0003', 'L-01-01', 'AVAILABLE', TRUE, '2023-11-06', 42.00),
    (320000000007, 10004, 101, 1003, 300000000002, 300000000002, 'S3-SCU-JA-0004', 'A-02-01', 'AVAILABLE', TRUE, '2025-04-16', 63.00),
    (320000000008, 10020, 101, 1003, 300000000002, 300000000002, 'S3-SCU-JA-0005', 'G-02-01', 'AVAILABLE', TRUE, '2025-08-20', 61.00),
    -- This Wangjiang copy is borrowed by reader 110000000001 from Site 1.
    (320000000009, 10001, 101, 1001, 300000000003, 300000000003, 'S3-SCU-WJ-0001', 'A-01-01', 'BORROWED', TRUE, '2024-03-01', 59.00),
    (320000000010, 10003, 101, 1001, 300000000003, 300000000003, 'S3-SCU-WJ-0002', 'A-01-02', 'AVAILABLE', TRUE, '2025-05-12', 76.00),
    (320000000011, 10011, 101, 1001, 300000000003, 300000000003, 'S3-SCU-WJ-0003', 'L-02-01', 'AVAILABLE', TRUE, '2023-11-06', 42.00)
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
    (330000000001, 310000000001, 1002, 10003, 320000000003,
        3, 300000000001, NULL, 'LOCAL',
        '2026-10-05 13:00:00+08', '2026-11-04 23:59:59+08', NULL,
        'BORROWING', 0, 0.00),
    (330000000002, 310000000002, 1003, 10011, 320000000006,
        3, 300000000002, 300000000002, 'LOCAL',
        '2026-06-01 10:00:00+08', '2026-07-01 23:59:59+08',
        '2026-06-25 15:20:00+08', 'RETURNED', 0, 0.00),
    -- Cross-campus case: a Wangjiang reader borrows a Jiang'an copy.
    (330000000003, 310000000004, 1001, 10017, 320000000001,
        3, 300000000002, NULL, 'CROSS_CAMPUS',
        '2026-10-03 11:00:00+08', '2026-11-02 23:59:59+08', NULL,
        'BORROWING', 0, 0.00)
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
