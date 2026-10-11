-- Coordinator database schema.
-- PostgreSQL 17 + PostGIS 3.5
-- Core tables: site_node, university, campus, category, book_catalog.

BEGIN;

CREATE TABLE IF NOT EXISTS site_node (
    site_id SMALLINT PRIMARY KEY,
    site_name VARCHAR(100) NOT NULL UNIQUE,
    service_url VARCHAR(500) NOT NULL,
    database_host VARCHAR(255) NOT NULL,
    database_port INTEGER NOT NULL DEFAULT 5432,
    database_name VARCHAR(100) NOT NULL UNIQUE,
    region_name VARCHAR(100),
    region_geometry GEOMETRY(MULTIPOLYGON, 4326),
    site_status VARCHAR(30) NOT NULL DEFAULT 'OFFLINE',
    last_heartbeat TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_site_id CHECK (site_id BETWEEN 1 AND 3),
    CONSTRAINT chk_site_port CHECK (database_port BETWEEN 1 AND 65535),
    CONSTRAINT chk_site_status CHECK (
        site_status IN ('ONLINE', 'OFFLINE', 'ERROR')
    ),
    CONSTRAINT chk_site_region_valid CHECK (
        region_geometry IS NULL OR ST_IsValid(region_geometry)
    )
);

CREATE INDEX IF NOT EXISTS idx_site_region_geometry
    ON site_node USING GIST (region_geometry);

CREATE INDEX IF NOT EXISTS idx_site_status
    ON site_node (site_status);

CREATE TABLE IF NOT EXISTS university (
    university_id BIGINT PRIMARY KEY,
    university_name VARCHAR(200) NOT NULL UNIQUE,
    short_name VARCHAR(100),
    address VARCHAR(500),
    website VARCHAR(500),
    phone VARCHAR(50),
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_university_status CHECK (
        status IN ('ACTIVE', 'DISABLED')
    )
);

CREATE TABLE IF NOT EXISTS campus (
    campus_id BIGINT PRIMARY KEY,
    university_id BIGINT NOT NULL,
    campus_name VARCHAR(200) NOT NULL,
    address VARCHAR(500),
    longitude NUMERIC(10, 7) NOT NULL,
    latitude NUMERIC(10, 7) NOT NULL,
    center_location GEOGRAPHY(POINT, 4326) NOT NULL,
    boundary GEOMETRY(POLYGON, 4326),
    site_id SMALLINT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_campus_university
        FOREIGN KEY (university_id)
        REFERENCES university (university_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_campus_site
        FOREIGN KEY (site_id)
        REFERENCES site_node (site_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT uq_campus_name
        UNIQUE (university_id, campus_name),
    CONSTRAINT chk_campus_longitude CHECK (
        longitude BETWEEN -180 AND 180
    ),
    CONSTRAINT chk_campus_latitude CHECK (
        latitude BETWEEN -90 AND 90
    ),
    CONSTRAINT chk_campus_boundary_valid CHECK (
        boundary IS NULL OR ST_IsValid(boundary)
    ),
    CONSTRAINT chk_campus_status CHECK (
        status IN ('ACTIVE', 'DISABLED')
    )
);

CREATE INDEX IF NOT EXISTS idx_campus_university
    ON campus (university_id);

CREATE INDEX IF NOT EXISTS idx_campus_site
    ON campus (site_id);

CREATE INDEX IF NOT EXISTS idx_campus_center_location
    ON campus USING GIST (center_location);

CREATE INDEX IF NOT EXISTS idx_campus_boundary
    ON campus USING GIST (boundary);

CREATE TABLE IF NOT EXISTS category (
    category_id BIGINT PRIMARY KEY,
    category_name VARCHAR(200) NOT NULL,
    parent_id BIGINT,
    description VARCHAR(1000),
    sort_order INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    CONSTRAINT fk_category_parent
        FOREIGN KEY (parent_id)
        REFERENCES category (category_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_category_not_self CHECK (
        parent_id IS NULL OR parent_id <> category_id
    ),
    CONSTRAINT chk_category_sort_order CHECK (
        sort_order >= 0
    ),
    CONSTRAINT chk_category_status CHECK (
        status IN ('ACTIVE', 'DISABLED')
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_category_root_name
    ON category (category_name)
    WHERE parent_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_category_child_name
    ON category (parent_id, category_name)
    WHERE parent_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_category_parent
    ON category (parent_id);

CREATE TABLE IF NOT EXISTS book_catalog (
    book_id BIGINT PRIMARY KEY,
    isbn VARCHAR(30),
    title VARCHAR(500) NOT NULL,
    author VARCHAR(500),
    translator VARCHAR(500),
    publisher VARCHAR(300),
    publish_year INTEGER,
    edition VARCHAR(100),
    category_id BIGINT NOT NULL,
    language VARCHAR(50),
    page_count INTEGER,
    summary TEXT,
    keywords VARCHAR(1000),
    cover_url VARCHAR(1000),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_book_category
        FOREIGN KEY (category_id)
        REFERENCES category (category_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_book_publish_year CHECK (
        publish_year IS NULL OR publish_year BETWEEN 1000 AND 9999
    ),
    CONSTRAINT chk_book_page_count CHECK (
        page_count IS NULL OR page_count > 0
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_book_isbn
    ON book_catalog (isbn)
    WHERE isbn IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_book_title
    ON book_catalog (title);

CREATE INDEX IF NOT EXISTS idx_book_author
    ON book_catalog (author);

CREATE INDEX IF NOT EXISTS idx_book_category
    ON book_catalog (category_id);

CREATE TABLE IF NOT EXISTS user_account (
    account_id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    reader_id BIGINT,
    home_site_id SMALLINT,
    managed_site_id SMALLINT,
    account_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_account_home_site FOREIGN KEY (home_site_id)
        REFERENCES site_node (site_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_account_managed_site FOREIGN KEY (managed_site_id)
        REFERENCES site_node (site_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_account_role CHECK (
        role IN ('STUDENT', 'SITE_ADMIN', 'ADMIN')
    ),
    CONSTRAINT chk_account_status CHECK (
        account_status IN ('ACTIVE', 'DISABLED')
    ),
    CONSTRAINT chk_account_role_scope CHECK (
        (role = 'STUDENT' AND reader_id IS NOT NULL
            AND home_site_id IS NOT NULL AND managed_site_id IS NULL)
        OR
        (role = 'SITE_ADMIN' AND reader_id IS NULL
            AND home_site_id IS NULL AND managed_site_id IS NOT NULL)
        OR
        (role = 'ADMIN' AND reader_id IS NULL
            AND home_site_id IS NULL AND managed_site_id IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_account_role_site
    ON user_account (role, managed_site_id);

COMMENT ON TABLE site_node IS
    'Data-node connection, status, and geographical management region.';
COMMENT ON TABLE university IS
    'Global university information; a university is not bound to one site.';
COMMENT ON TABLE campus IS
    'Global campus GIS information and authoritative site routing.';
COMMENT ON TABLE category IS
    'Hierarchical book category.';
COMMENT ON TABLE book_catalog IS
    'Global bibliographic catalog stored at the coordinator.';
COMMENT ON TABLE user_account IS
    'Central authentication accounts and role/site authorization scope.';

COMMIT;
