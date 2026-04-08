import { useState } from "react";
import { motion } from "framer-motion";
import { Leaf, Mail, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import { z } from "zod";

const emailSchema = z.object({
  email: z.string().trim().email("Please enter a valid email"),
});

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = emailSchema.safeParse({ email });
    if (!result.success) {
      setError(result.error.errors[0].message);
      return;
    }
    setError("");
    setIsSubmitting(true);
    const { error: resetError } = await supabase.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    setIsSubmitting(false);
    if (resetError) {
      toast.error(resetError.message);
    } else {
      setSent(true);
    }
  };

  return (
    <div className="min-h-screen gradient-hero flex items-center justify-center px-6">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-6">
            <Leaf className="h-8 w-8 text-primary" />
            <span className="font-display text-2xl text-foreground">Ember</span>
          </Link>
          <h1 className="text-3xl font-display text-foreground mb-2">Reset your password</h1>
          <p className="text-muted-foreground">We'll send you a link to reset it</p>
        </div>

        {sent ? (
          <div className="bg-card rounded-2xl border border-border p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-sage-light flex items-center justify-center mx-auto mb-4">
              <Mail className="h-8 w-8 text-primary" />
            </div>
            <h2 className="font-display text-xl text-foreground mb-2">Check your email</h2>
            <p className="text-sm text-muted-foreground mb-6">We've sent a password reset link to <strong>{email}</strong></p>
            <Link to="/login">
              <Button variant="outline" className="gap-2">
                <ArrowLeft className="h-4 w-4" /> Back to login
              </Button>
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="bg-card rounded-2xl border border-border p-8 space-y-5">
            <div>
              <Label className="text-sm font-medium text-foreground">Email</Label>
              <div className="relative mt-1.5">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10"
                />
              </div>
              {error && <p className="text-xs text-destructive mt-1">{error}</p>}
            </div>
            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting ? "Sending..." : "Send Reset Link"}
            </Button>
          </form>
        )}

        <p className="text-center text-sm text-muted-foreground mt-6">
          <Link to="/login" className="text-primary font-medium hover:underline flex items-center justify-center gap-1">
            <ArrowLeft className="h-3 w-3" /> Back to login
          </Link>
        </p>
      </motion.div>
    </div>
  );
};

export default ForgotPassword;
