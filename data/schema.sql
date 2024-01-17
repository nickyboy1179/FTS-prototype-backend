-- DROP TABLE IF EXISTS location;

-- CREATE TABLE location (
--     location_id INTEGER PRIMARY KEY AUTOINCREMENT,
--     street_name VARCHAR(255) NOT NULL,
--     zip_code VARCHAR(255) NOT NULL,
--     house_number INTEGER NOT NULL,
--     name VARCHAR(255),
-- );

-- DROP TABLE IF EXISTS categories;
--
-- CREATE TABLE categories (
--     category_id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name VARCHAR(255) NOT NULL,
-- );
--
DROP TABLE IF EXISTS events;

CREATE TABLE events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    organizers_notes TEXT,
    start_time TIME,
    end_time TIME,
    location_id INTEGER NOT NULL,
    FOREIGN KEY (location_id) REFERENCES location(location_id)
);
--
--
--
-- DROP TABLE IF EXISTS event_days;
--
-- CREATE TABLE event_days(
--     event_days_id INTEGER PRIMARY KEY AUTOINCREMENT,
--     event_id INTEGER NOT NULL,
--     day_of_week INTEGER NOT NULL,
--     week_of_month INTEGER,
--     FOREIGN KEY (event_id) REFERENCES events(event_id)
-- );
--
-- DROP TABLE IF EXISTS events_categories;
--
-- CREATE TABLE events_categories (
--     category_id INT NOT NULL,
--     event_id INT NOT NULL,
--     PRIMARY KEY (category_id, event_id),
--     FOREIGN KEY (category_id) REFERENCES categories(category_id),
--     FOREIGN KEY (event_id) REFERENCES events(event_id)
-- );

