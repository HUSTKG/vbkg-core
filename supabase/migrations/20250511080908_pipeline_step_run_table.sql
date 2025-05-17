-- 1. Create new pipeline_steps table
CREATE TABLE IF NOT EXISTS public.pipeline_steps (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  pipeline_id UUID REFERENCES public.pipelines(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  step_type TEXT NOT NULL,
  config JSONB NOT NULL,
  run_order INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- 2. Create new pipeline_step_runs table
CREATE TABLE IF NOT EXISTS public.pipeline_step_runs (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  pipeline_run_id UUID REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
  step_id UUID REFERENCES public.pipeline_steps(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
  start_time TIMESTAMP WITH TIME ZONE,
  end_time TIMESTAMP WITH TIME ZONE,
  run_order INTEGER NOT NULL,
  input_data JSONB,
  output_data JSONB,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  celery_task_id TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, now()) NOT NULL
);

-- 3. Add new columns to pipeline_runs table
ALTER TABLE public.pipeline_runs
ADD COLUMN input_parameters JSONB,
ADD COLUMN result JSONB,
ADD COLUMN celery_task_id TEXT;

-- 4. Create indexes for performance
CREATE INDEX idx_pipeline_steps_pipeline_id ON public.pipeline_steps(pipeline_id);
CREATE INDEX idx_pipeline_step_runs_pipeline_run_id ON public.pipeline_step_runs(pipeline_run_id);
CREATE INDEX idx_pipeline_step_runs_step_id ON public.pipeline_step_runs(step_id);
CREATE INDEX idx_pipeline_runs_pipeline_id ON public.pipeline_runs(pipeline_id);
CREATE INDEX idx_pipeline_runs_status ON public.pipeline_runs(status);

-- 5. Drop steps column after migration (optional - you might want to keep it temporarily)
ALTER TABLE public.pipelines DROP COLUMN steps;
