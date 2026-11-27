-- BASELINE: naive schema, only primary keys, no partitioning
CREATE TABLE users (
    id          integer PRIMARY KEY,
    email       text NOT NULL,
    created_at  timestamptz NOT NULL
);
CREATE TABLE projects (
    id          integer PRIMARY KEY,
    owner_id    integer NOT NULL,
    name        text NOT NULL,
    created_at  timestamptz NOT NULL
);
CREATE TABLE tags (
    id   integer PRIMARY KEY,
    name text NOT NULL
);
CREATE TABLE tasks (
    id          bigint PRIMARY KEY,
    user_id     integer NOT NULL,
    project_id  integer NOT NULL,
    title       text NOT NULL,
    status      text NOT NULL,            -- todo / doing / done
    priority    smallint NOT NULL,
    due_date    date,
    created_at  timestamptz NOT NULL,
    updated_at  timestamptz NOT NULL
);
CREATE TABLE task_tags (
    task_id bigint  NOT NULL,
    tag_id  integer NOT NULL,
    PRIMARY KEY (task_id, tag_id)
);
