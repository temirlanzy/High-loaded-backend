\set uid random(1, 20000)
SELECT id, title, due_date, priority FROM tasks WHERE user_id = :uid AND status <> 'done' ORDER BY due_date LIMIT 20;
