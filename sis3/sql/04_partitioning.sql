-- S2: RANGE partitioning of tasks by created_at (monthly), online-style swap
\timing on
BEGIN;
CREATE TABLE tasks_part (
    id          bigint      NOT NULL,
    user_id     integer     NOT NULL,
    project_id  integer     NOT NULL,
    title       text        NOT NULL,
    status      text        NOT NULL,
    priority    smallint    NOT NULL,
    due_date    date,
    created_at  timestamptz NOT NULL,
    updated_at  timestamptz NOT NULL,
    PRIMARY KEY (id, created_at)            -- PK of a partitioned table must include the partition key
) PARTITION BY RANGE (created_at);

DO $$
DECLARE m date := date '2024-11-01';
BEGIN
  WHILE m < date '2027-02-01' LOOP
    EXECUTE format('CREATE TABLE tasks_p%s PARTITION OF tasks_part FOR VALUES FROM (%L) TO (%L)',
                   to_char(m,'YYYY_MM'), m, (m + interval '1 month')::date);
    m := (m + interval '1 month')::date;
  END LOOP;
END $$;
CREATE TABLE tasks_pdefault PARTITION OF tasks_part DEFAULT;

INSERT INTO tasks_part SELECT * FROM tasks;

DROP TABLE tasks;                           -- old indexes go away with it
ALTER TABLE tasks_part RENAME TO tasks;
ALTER INDEX tasks_part_pkey RENAME TO tasks_pkey;
COMMIT;

-- same indexes as in S1, now defined on the parent -> one small local index per partition
CREATE INDEX idx_tasks_user_open_due    ON tasks (user_id, due_date) WHERE status <> 'done';
CREATE INDEX idx_tasks_user_created     ON tasks (user_id, created_at DESC);
CREATE INDEX idx_tasks_created_status   ON tasks (created_at) INCLUDE (status);
VACUUM (ANALYZE) tasks;
CHECKPOINT;
