\set uid random(1, 20000)
SELECT count(*) FROM tasks WHERE user_id = :uid AND status <> 'done' AND due_date < current_date;
