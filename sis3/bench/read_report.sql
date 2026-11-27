SELECT status, count(*) FROM tasks WHERE created_at >= now() - interval '30 days' GROUP BY status;
