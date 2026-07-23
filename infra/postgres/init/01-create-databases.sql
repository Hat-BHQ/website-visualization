SELECT 'CREATE DATABASE auth_db OWNER "' || current_user || '"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'auth_db')\gexec

SELECT 'CREATE DATABASE hqa_db OWNER "' || current_user || '"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'hqa_db')\gexec

SELECT 'CREATE DATABASE hqs_db OWNER "' || current_user || '"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'hqs_db')\gexec
