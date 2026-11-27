\pset pager off
\echo '=== Q1 list open tasks of a user (ORDER BY due_date LIMIT 20)'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT id, title, due_date, priority FROM tasks WHERE user_id = 777 AND status <> 'done' ORDER BY due_date LIMIT 20;
\echo '=== Q2 overdue count'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM tasks WHERE user_id = 777 AND status <> 'done' AND due_date < current_date;
\echo '=== Q3 tasks of a user with tag'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT t.id, t.title FROM tasks t JOIN task_tags tt ON tt.task_id = t.id WHERE t.user_id = 777 AND tt.tag_id = 7 LIMIT 20;
\echo '=== Q4 30-day report'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT status, count(*) FROM tasks WHERE created_at >= now() - interval '30 days' GROUP BY status;
\echo '=== Q5 update by id'
BEGIN;
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) UPDATE tasks SET status = 'done', updated_at = now() WHERE id = 1234567;
ROLLBACK;
