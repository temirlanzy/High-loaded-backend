\set uid random(1, 20000)
\set tag random(1, 50)
SELECT t.id, t.title FROM tasks t JOIN task_tags tt ON tt.task_id = t.id WHERE t.user_id = :uid AND tt.tag_id = :tag LIMIT 20;
