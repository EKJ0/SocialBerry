
-- Create check_ins table
CREATE TABLE public.check_ins (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  energy INTEGER NOT NULL CHECK (energy >= 1 AND energy <= 10),
  sleep INTEGER NOT NULL CHECK (sleep >= 1 AND sleep <= 10),
  overwhelm INTEGER NOT NULL CHECK (overwhelm >= 1 AND overwhelm <= 10),
  motivation INTEGER NOT NULL CHECK (motivation >= 1 AND motivation <= 10),
  focus INTEGER NOT NULL CHECK (focus >= 1 AND focus <= 10),
  withdrawal INTEGER NOT NULL CHECK (withdrawal >= 1 AND withdrawal <= 10),
  burnout_score INTEGER NOT NULL CHECK (burnout_score >= 0 AND burnout_score <= 100),
  checked_in_at DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- One check-in per user per day
CREATE UNIQUE INDEX idx_check_ins_user_date ON public.check_ins (user_id, checked_in_at);

-- Enable RLS
ALTER TABLE public.check_ins ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own check-ins"
  ON public.check_ins FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own check-ins"
  ON public.check_ins FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own check-ins"
  ON public.check_ins FOR DELETE
  USING (auth.uid() = user_id);
