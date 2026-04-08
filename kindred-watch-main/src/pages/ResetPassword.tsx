import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Leaf, Lock, Eye, EyeOff, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link, useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import { z } from "zod";

const passwordSchema = z.object({
  password: z.string().min(6, "Password must be at least 6 characters"),
});

const ResetPassword = () => {
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [isRecovery, setIsRecovery] = useState(false);

  useEffect(() => {
    const hash = window.location.hash;
    if (hash.includes("type=recovery")) {
      setIsRecovery(true);
    }

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      if (event === "PASSWORD_RECOVERY") {
        setIsRecovery(true);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = passwordSchema.safeParse({ password });
    if (!result.success) {
      setError(result.error.errors[0].message);
      return;
    }
    setError("");
    setIsSubmitting(true);
    const { error: updateError } = await supabase.auth.updateUser({ password });
    setIsSubmitting(false);
    if (updateError) {
      toast.error(updateError.message);
    } else {
      toast.success("Password updated successfully!");
      navigate("/dashboard");
    }
  };

  if (!isRecovery) {
    return (
      <div className="min-h-screen gradient-hero flex items-center justify-center px-6">
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} className="text-center max-w-md">
          <Leaf className="h-8 w-8 text-primary mx-auto mb-4" />
          <h1 className="text-2xl font-display text-foreground mb-2">Invalid reset link</h1>
          <p className="text-muted-foreground mb-6">This password reset link is invalid or expired.</p>
          <Link to="/forgot-password">
            <Button>Request a new link</Button>
          </Link>
        </motion.div>
      </div>
    );
  }

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
          <h1 className="text-3xl font-display text-foreground mb-2">Set new password</h1>
          <p className="text-muted-foreground">Choose a new password for your account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-card rounded-2xl border border-border p-8 space-y-5">
          <div>
            <Label className="text-sm font-medium text-foreground">New Password</Label>
            <div className="relative mt-1.5">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type={showPassword ? "text" : "password"}
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10 pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {error && <p className="text-xs text-destructive mt-1">{error}</p>}
          </div>
          <Button type="submit" disabled={isSubmitting} className="w-full gap-2">
            {isSubmitting ? "Updating..." : <><Check className="h-4 w-4" /> Update Password</>}
          </Button>
        </form>
      </motion.div>
    </div>
  );
};

export default ResetPassword;
