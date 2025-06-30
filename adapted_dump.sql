CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    username TEXT,
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT ix_users_telegram_id UNIQUE (telegram_id)
);

CREATE TABLE sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    is_available BOOLEAN NOT NULL,
    last_checked DATETIME,
    last_notified DATETIME,
    CONSTRAINT _user_url_uc UNIQUE (user_id, url),
    CONSTRAINT sites_pkey PRIMARY KEY (id),
    CONSTRAINT sites_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    CONSTRAINT system_settings_key UNIQUE (key),
    CONSTRAINT system_settings_pkey PRIMARY KEY (id)
);

CREATE INDEX ix_sites_url ON sites (url);
CREATE INDEX ix_sites_user_id ON sites (user_id);

INSERT INTO users (id, telegram_id, username) VALUES
(1, 11867909, 'webjesus'),
(2, 1761909893, 'holdonb'),
(3, 5128947714, 'digitalilia'),
(4, 701412765, 'RuMarketolog'),
(5, 415383262, 'userxveronixxx'),
(6, 144403075, 'sergey_usachev'),
(7, 1946421717, 'Diam0nd777'),
(8, 930005125, 'savateeva_zlata'),
(41, 32370544, 'stepanov_iv_n');

INSERT INTO sites (id, url, user_id, is_available, last_checked, last_notified) VALUES
(1, 'https://webjesus.ru', 1, 1, '2025-06-30 07:54:05.46391', NULL),
(3, 'http://collabapr.com/', 1, 1, '2025-06-30 07:54:05.749001', NULL),
(44, 'https://vc.ru', 1, 1, '2025-06-30 07:54:06.425056', NULL),
(4, 'https://dostupsmile.ru/', 4, 1, '2025-06-30 07:54:06.721137', NULL),
(5, 'https://dostupstom24.ru', 5, 1, '2025-06-30 07:54:07.980188', NULL),
(7, 'https://dostupsmile.ru/', 5, 1, '2025-06-30 07:54:08.092903', NULL),
(6, 'https://mpfinassist.io', 6, 1, '2025-06-30 07:54:08.395242', NULL),
(8, 'https://miradent-58.ru/', 8, 1, '2025-06-30 07:54:08.888221', NULL),
(41, 'https://dostupstom24.ru', 41, 1, '2025-06-30 07:54:09.342892', NULL),
(42, 'https://dostupsmile.ru', 41, 1, '2025-06-30 07:54:09.410481', NULL),
(43, 'https://nsk.stomdostup.ru/', 41, 1, '2025-06-30 07:54:10.015531', NULL);

INSERT INTO system_settings (id, key, value) VALUES
(1, 'check_interval_minutes', '60');

INSERT INTO sqlite_sequence (name, seq) VALUES ('users', 41);
INSERT INTO sqlite_sequence (name, seq) VALUES ('sites', 76);
INSERT INTO sqlite_sequence (name, seq) VALUES ('system_settings', 1);