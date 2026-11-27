-- S1: indexes designed for the workload (only what the queries need)
-- Q1+Q2: partial index = only unfinished tasks, ordered by due_date per user
CREATE INDEX idx_tasks_user_open_due ON tasks (user_id, due_date) WHERE status <> 'done';
-- Q3: find all tasks of a user (then PK lookup in task_tags); also serves "recent tasks of user"
CREATE INDEX idx_tasks_user_created ON tasks (user_id, created_at DESC);
-- Q4: covering index -> index-only scan, table is never touched
CREATE INDEX idx_tasks_created_status ON tasks (created_at) INCLUDE (status);
VACUUM (ANALYZE) tasks;
CHECKPOINT;
