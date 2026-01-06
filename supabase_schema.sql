-- Create the table for storing daily news summaries
create table if not exists news_summaries (
  date date primary key,
  content text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS) is recommended practice,
-- though for this simple server-side use case with service_role key, it's optional but good for future proofing.
alter table news_summaries enable row level security;

-- Create a policy that allows read access to everyone (if you want public archive)
-- Or you can restrict it. For now, we allow the service_role (backend) to do everything.
-- By default, service_role bypasses RLS, so explicit policies are mainly for client-side access.
-- If you plan to read this directly from frontend later, un-comment below:
-- create policy "Enable read access for all users" on news_summaries for select using (true);
