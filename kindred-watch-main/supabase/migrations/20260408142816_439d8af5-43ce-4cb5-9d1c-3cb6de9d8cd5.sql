
-- Create trusted_contacts table
CREATE TABLE public.trusted_contacts (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  relationship TEXT NOT NULL DEFAULT 'friend',
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined')),
  alert_threshold INTEGER NOT NULL DEFAULT 75 CHECK (alert_threshold >= 0 AND alert_threshold <= 100),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.trusted_contacts ENABLE ROW LEVEL SECURITY;

-- Users can only view their own contacts
CREATE POLICY "Users can view their own trusted contacts"
  ON public.trusted_contacts FOR SELECT
  USING (auth.uid() = user_id);

-- Users can create their own contacts
CREATE POLICY "Users can create their own trusted contacts"
  ON public.trusted_contacts FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can update their own contacts
CREATE POLICY "Users can update their own trusted contacts"
  ON public.trusted_contacts FOR UPDATE
  USING (auth.uid() = user_id);

-- Users can delete their own contacts
CREATE POLICY "Users can delete their own trusted contacts"
  ON public.trusted_contacts FOR DELETE
  USING (auth.uid() = user_id);

-- Timestamp trigger
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public;

CREATE TRIGGER update_trusted_contacts_updated_at
  BEFORE UPDATE ON public.trusted_contacts
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
