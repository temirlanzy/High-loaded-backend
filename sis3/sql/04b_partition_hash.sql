-- S2b: re-partition tasks by HASH(user_id), 16 partitions (workload: 70% of reads filter by user_id)
BEGIN;
CREATE TABLE tasks_h (
    id          bigint      NOT NULL,
    user_id     integer     NOT NULL,
    project_id  integer     NOT NULL,
    title       text        NOT NULL,
    status      text        NOT NULL,
    priority    smallint    NOT NULL,
    due_date    date,
    created_at  timestamptz NOT NULL,
    updated_at  timestamptz NOT NULL,
    PRIMARY KEY (id, user_id)               -- must include the partition key; id comes from a sequence, so it stays unique in practice
) PARTITION BY HASH (user_id);
DO $$ BEGIN
  FOR i IN 0..15 LOOP
    EXECUTE format('CREATE TABLE tasks_h%s PARTITION OF tasks_h FOR VALUES WITH (MODULUS 16, REMAINDER %s)', i, i);
  END LOOP;
END $$;
INSERT INTO tasks_h SELECT * FROM tasks;
DROP TABLE tasks;
ALTER TABLE tasks_h RENAME TO tasks;
ALTER INDEX tasks_h_pkey RENAME TO tasks_pkey;
COMMIT;
CREATE INDEX idx_tasks_user_open_due  ON tasks (user_id, due_date) WHERE status <> 'done';
CREATE INDEX idx_tasks_user_created   ON tasks (user_id, created_at DESC);
CREATE INDEX idx_tasks_created_status ON tasks (created_at) INCLUDE (status);
VACUUM (ANALYZE) tasks;
CHECKPOINT;
