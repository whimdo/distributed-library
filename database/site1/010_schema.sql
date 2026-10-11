-- Data-site database schema.
-- This same schema is used by Site 1, Site 2, and Site 3.
-- Cross-database references are validated by the coordinator service.

BEGIN;

CREATE TABLE IF NOT EXISTS library_fragment (
    library_id BIGINT PRIMARY KEY,
    university_id BIGINT NOT NULL,
    campus_id BIGINT NOT NULL,
    library_name VARCHAR(200) NOT NULL,
    address VARCHAR(500),
    longitude NUMERIC(10, 7) NOT NULL,
    latitude NUMERIC(10, 7) NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    open_time TIME,
    close_time TIME,
    phone VARCHAR(50),
    total_seats INTEGER,
    service_radius_m INTEGER NOT NULL DEFAULT 3000,
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_library_name
        UNIQUE (campus_id, library_name),
    CONSTRAINT chk_library_longitude CHECK (
        longitude BETWEEN -180 AND 180
    ),
    CONSTRAINT chk_library_latitude CHECK (
        latitude BETWEEN -90 AND 90
    ),
    CONSTRAINT chk_library_seats CHECK (
        total_seats IS NULL OR total_seats >= 0
    ),
    CONSTRAINT chk_library_service_radius CHECK (
        service_radius_m > 0 AND service_radius_m <= 100000
    ),
    CONSTRAINT chk_library_hours CHECK (
        open_time IS NULL
        OR close_time IS NULL
        OR open_time <> close_time
    ),
    CONSTRAINT chk_library_status CHECK (
        status IN ('OPEN', 'CLOSED', 'MAINTENANCE')
    )
);

-- Compatibility migration for databases created before service_radius_m existed.
ALTER TABLE library_fragment
    ADD COLUMN IF NOT EXISTS service_radius_m INTEGER NOT NULL DEFAULT 3000;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'library_fragment'::regclass
          AND conname = 'chk_library_service_radius'
    ) THEN
        ALTER TABLE library_fragment
            ADD CONSTRAINT chk_library_service_radius
            CHECK (service_radius_m > 0 AND service_radius_m <= 100000);
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_library_location
    ON library_fragment USING GIST (location);

CREATE INDEX IF NOT EXISTS idx_library_campus
    ON library_fragment (campus_id);

CREATE INDEX IF NOT EXISTS idx_library_university
    ON library_fragment (university_id);

CREATE TABLE IF NOT EXISTS reader_fragment (
    reader_id BIGINT PRIMARY KEY,
    home_university_id BIGINT NOT NULL,
    home_campus_id BIGINT NOT NULL,
    student_no VARCHAR(100) NOT NULL,
    network_card_no VARCHAR(100) NOT NULL,
    reader_name VARCHAR(100) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(200),
    password_hash VARCHAR(255) NOT NULL,
    reader_type VARCHAR(30) NOT NULL,
    network_permission BOOLEAN NOT NULL DEFAULT TRUE,
    max_borrow_count INTEGER NOT NULL DEFAULT 10,
    current_borrow_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_reader_student
        UNIQUE (home_university_id, student_no),
    CONSTRAINT uq_reader_network_card
        UNIQUE (network_card_no),
    CONSTRAINT chk_reader_type CHECK (
        reader_type IN ('UNDERGRADUATE', 'POSTGRADUATE', 'TEACHER')
    ),
    CONSTRAINT chk_reader_borrow_counts CHECK (
        max_borrow_count >= 0
        AND current_borrow_count >= 0
        AND current_borrow_count <= max_borrow_count
    ),
    CONSTRAINT chk_reader_status CHECK (
        status IN ('ACTIVE', 'FROZEN', 'DISABLED')
    )
);

CREATE INDEX IF NOT EXISTS idx_reader_home_campus
    ON reader_fragment (home_campus_id);

CREATE INDEX IF NOT EXISTS idx_reader_home_university
    ON reader_fragment (home_university_id);

CREATE INDEX IF NOT EXISTS idx_reader_name
    ON reader_fragment (reader_name);

CREATE TABLE IF NOT EXISTS book_copy_fragment (
    copy_id BIGINT PRIMARY KEY,
    book_id BIGINT NOT NULL,
    owner_university_id BIGINT NOT NULL,
    owner_campus_id BIGINT NOT NULL,
    owner_library_id BIGINT NOT NULL,
    current_library_id BIGINT NOT NULL,
    barcode VARCHAR(100) NOT NULL UNIQUE,
    shelf_location VARCHAR(100),
    copy_status VARCHAR(30) NOT NULL DEFAULT 'AVAILABLE',
    allow_cross_borrow BOOLEAN NOT NULL DEFAULT TRUE,
    acquisition_date DATE,
    price NUMERIC(10, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_copy_owner_library
        FOREIGN KEY (owner_library_id)
        REFERENCES library_fragment (library_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_copy_status CHECK (
        copy_status IN (
            'AVAILABLE',
            'BORROWED',
            'IN_TRANSIT',
            'REPAIR',
            'LOST'
        )
    ),
    CONSTRAINT chk_copy_price CHECK (
        price IS NULL OR price >= 0
    )
);

CREATE INDEX IF NOT EXISTS idx_copy_book_status
    ON book_copy_fragment (book_id, copy_status);

CREATE INDEX IF NOT EXISTS idx_copy_current_library
    ON book_copy_fragment (current_library_id, copy_status);

CREATE INDEX IF NOT EXISTS idx_copy_owner_campus
    ON book_copy_fragment (owner_campus_id);

CREATE INDEX IF NOT EXISTS idx_copy_owner_university
    ON book_copy_fragment (owner_university_id);

CREATE TABLE IF NOT EXISTS borrow_record_fragment (
    borrow_id BIGINT PRIMARY KEY,
    reader_id BIGINT NOT NULL,
    reader_home_campus_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    copy_id BIGINT NOT NULL,
    copy_owner_site_id SMALLINT NOT NULL,
    checkout_library_id BIGINT NOT NULL,
    return_library_id BIGINT,
    borrow_type VARCHAR(30) NOT NULL,
    borrow_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_time TIMESTAMPTZ NOT NULL,
    return_time TIMESTAMPTZ,
    borrow_status VARCHAR(30) NOT NULL DEFAULT 'BORROWING',
    renew_count INTEGER NOT NULL DEFAULT 0,
    fine_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_borrow_reader
        FOREIGN KEY (reader_id)
        REFERENCES reader_fragment (reader_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_borrow_owner_site CHECK (
        copy_owner_site_id BETWEEN 1 AND 3
    ),
    CONSTRAINT chk_borrow_type CHECK (
        borrow_type IN ('LOCAL', 'CROSS_CAMPUS', 'CROSS_UNIVERSITY')
    ),
    CONSTRAINT chk_borrow_status CHECK (
        borrow_status IN ('BORROWING', 'RETURNED', 'OVERDUE', 'LOST')
    ),
    CONSTRAINT chk_borrow_due_time CHECK (
        due_time > borrow_time
    ),
    CONSTRAINT chk_borrow_return_time CHECK (
        (borrow_status = 'RETURNED' AND return_time IS NOT NULL)
        OR
        (
            borrow_status IN ('BORROWING', 'OVERDUE', 'LOST')
            AND return_time IS NULL
        )
    ),
    CONSTRAINT chk_borrow_renew_count CHECK (
        renew_count >= 0
    ),
    CONSTRAINT chk_borrow_fine CHECK (
        fine_amount >= 0
    )
);

CREATE INDEX IF NOT EXISTS idx_borrow_reader_status
    ON borrow_record_fragment (reader_id, borrow_status, due_time);

CREATE INDEX IF NOT EXISTS idx_borrow_copy
    ON borrow_record_fragment (copy_id, borrow_status);

CREATE INDEX IF NOT EXISTS idx_borrow_due
    ON borrow_record_fragment (due_time)
    WHERE borrow_status IN ('BORROWING', 'OVERDUE');

CREATE UNIQUE INDEX IF NOT EXISTS uq_borrow_active_copy_local
    ON borrow_record_fragment (copy_id)
    WHERE borrow_status IN ('BORROWING', 'OVERDUE');

COMMENT ON TABLE library_fragment IS
    'Horizontally partitioned library and precise GIS location.';
COMMENT ON TABLE reader_fragment IS
    'Readers partitioned by home campus site.';
COMMENT ON TABLE book_copy_fragment IS
    'Physical copies partitioned by owner campus site.';
COMMENT ON TABLE borrow_record_fragment IS
    'Borrow records partitioned by reader home-campus site.';

COMMIT;
