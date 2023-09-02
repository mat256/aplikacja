DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS data;
DROP TABLE IF EXISTS insulin;
DROP TABLE IF EXISTS file;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE personal (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  surname TEXT NOT NULL,
  pesel INTEGER NOT NULL,
  birth_date DATE NOT NULL,
  day_start TEXT,
  day_end TEXT,
  phone INTEGER,
  email TEXT,
  adress TEXT,
  FOREIGN KEY (author_id) REFERENCES user (id)
);


CREATE TABLE data (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  custom_date TIMESTAMP NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  glucose INTEGER NOT NULL,
  activity TEXT ,
  info TEXT ,
  stat TEXT DEFAULT 'success',
  from_file INTEGER DEFAULT 0 NOT NULL,
  file_id INTEGER,
  FOREIGN KEY (author_id) REFERENCES user (id)
  FOREIGN KEY (file_id) REFERENCES file (id)
);

CREATE TABLE insulin (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  custom_date TIMESTAMP NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  amount INTEGER NOT NULL,
  type TEXT DEFAULT 'short',
  period INTEGER DEFAULT 0,
  from_file INTEGER DEFAULT 0 NOT NULL,
  file_id INTEGER,
  FOREIGN KEY (author_id) REFERENCES user (id)
  FOREIGN KEY (file_id) REFERENCES file (id)
);


CREATE TABLE file (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  uploaded TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TRIGGER add_glucose_stat_war AFTER INSERT ON data
WHEN (new.glucose<70 AND new.glucose>=60) OR (new.glucose>140 AND new.glucose<180)
  BEGIN
    UPDATE data SET stat = 'warning' WHERE id = new.id;
  END;

  CREATE TRIGGER add_glucose_stat_dan AFTER INSERT ON data
WHEN new.glucose>160 OR new.glucose<60
  BEGIN

    UPDATE data SET stat = 'danger' WHERE id = new.id;
  END;