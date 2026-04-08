import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Leaf, Zap, Moon, Brain, Heart, Eye, UserMinus, ArrowRight, ArrowLeft, Check, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/contexts/AuthContext";
import { calculateBurnoutScore } from "@/lib/burnout";

const dimensions = [
  { key: "energy", label: "Energy", description: "How energized do you feel right now?", icon: Zap, low: "Exhausted", high: "Energized" },
  { key: "sleep", label: "Sleep Quality", description: "How well did you sleep last night?", icon: Moon, low: "Terrible", high: "Great" },
  { key: "overwhelm", label: "Overwhelm", description: "How overwhelmed do you feel?", icon: Brain, low: "Calm", high: "Overwhelmed" },
  { key: "motivation", label: "Motivation", description: "How motivated are you today?", icon: Heart, low: "None", high: "Driven" },
  { key: "focus", label: "Focus", description: "How well can you concentrate?", icon: Eye, low: "Scattered", high: "Laser-focused" },
  { key: "withdrawal", label: "Social Withdrawal", description: "How much are you avoiding people?", icon: UserMinus, low: "Connected", high: "Isolated" },
];

const CheckIn = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [values, setValues] = useState<Record<string, number>>(
    Object.fromEntries(dimensions.map((d) => [d.key, 5]))
  );
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [burnoutResult, setBurnoutResult] = useState(0);

  const current = dimensions[step];
  const isLast = step === dimensions.length - 1;

  const handleSubmit = async () => {
    if (!user) return;
    setIsSubmitting(true);

    const score = calculateBurnoutScore({
      energy: values.energy,
      sleep: values.sleep,
      overwhelm: values.overwhelm,
      motivation: values.motivation,
      focus: values.focus,
      withdrawal: values.withdrawal,
    });

    const { error } = await supabase.from("check_ins").insert({
      user_id: user.id,
      energy: values.energy,
      sleep: values.sleep,
      overwhelm: values.overwhelm,
      motivation: values.motivation,
      focus: values.focus,
      withdrawal: values.withdrawal,
      burnout_score: score,
    });

    setIsSubmitting(false);

    if (error) {
      if (error.code === "23505") {
        toast.error("You've already checked in today. Come back tomorrow!");
      } else {
        toast.error("Failed to save check-in. Please try again.");
      }
      return;
    }

    setBurnoutResult(score);
    setSubmitted(true);
    toast.success("Check-in saved! Your burnout risk has been updated.");
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <Nav navigate={navigate} />
        <div className="flex-1 flex items-center justify-center px-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center max-w-md"
          >
            <div className="w-20 h-20 rounded-full bg-sage-light flex items-center justify-center mx-auto mb-6">
              <Sparkles className="h-10 w-10 text-primary" />
            </div>
            <h1 className="text-3xl font-display text-foreground mb-2">Check-in complete</h1>
            <p className="text-4xl font-display text-foreground mb-1">{burnoutResult}%</p>
            <p className="text-muted-foreground mb-8">burnout risk today</p>
            <div className="grid grid-cols-3 gap-3 mb-8">
              {dimensions.map((d) => (
                <div key={d.key} className="bg-card rounded-xl border border-border p-3 text-center">
                  <d.icon className="h-4 w-4 mx-auto text-primary mb-1" />
                  <p className="text-xs text-muted-foreground">{d.label}</p>
                  <p className="text-lg font-display text-foreground">{values[d.key]}</p>
                </div>
              ))}
            </div>
            <Button onClick={() => navigate("/dashboard")} className="gap-2">
              Back to Dashboard <ArrowRight className="h-4 w-4" />
            </Button>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Nav navigate={navigate} />

      <div className="flex-1 flex flex-col items-center justify-center px-6 pt-20 pb-12">
        {/* Progress */}
        <div className="w-full max-w-md mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Question {step + 1} of {dimensions.length}</span>
            <span className="text-sm font-medium text-foreground">{Math.round(((step + 1) / dimensions.length) * 100)}%</span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-primary rounded-full"
              animate={{ width: `${((step + 1) / dimensions.length) * 100}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>

        {/* Card */}
        <div className="w-full max-w-md">
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -40 }}
              transition={{ duration: 0.3 }}
              className="bg-card rounded-2xl border border-border p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-sage-light flex items-center justify-center">
                  <current.icon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h2 className="font-display text-2xl text-foreground">{current.label}</h2>
                  <p className="text-sm text-muted-foreground">{current.description}</p>
                </div>
              </div>

              {/* Value Display */}
              <div className="text-center mb-6">
                <motion.span
                  key={values[current.key]}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="text-6xl font-display text-foreground inline-block"
                >
                  {values[current.key]}
                </motion.span>
                <span className="text-2xl text-muted-foreground font-display">/10</span>
              </div>

              {/* Slider */}
              <div className="px-1 mb-4">
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={values[current.key]}
                  onChange={(e) => setValues((prev) => ({ ...prev, [current.key]: parseInt(e.target.value) }))}
                  className="w-full h-3 rounded-full appearance-none cursor-pointer accent-primary bg-muted
                    [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-7 [&::-webkit-slider-thumb]:h-7 
                    [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:shadow-lg
                    [&::-webkit-slider-thumb]:border-4 [&::-webkit-slider-thumb]:border-background
                    [&::-moz-range-thumb]:w-7 [&::-moz-range-thumb]:h-7 [&::-moz-range-thumb]:rounded-full 
                    [&::-moz-range-thumb]:bg-primary [&::-moz-range-thumb]:border-4 [&::-moz-range-thumb]:border-background"
                />
              </div>

              {/* Labels */}
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{current.low}</span>
                <span>{current.high}</span>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Navigation */}
        <div className="w-full max-w-md flex items-center justify-between mt-8">
          <Button
            variant="ghost"
            onClick={() => setStep((s) => s - 1)}
            disabled={step === 0}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" /> Back
          </Button>

          {/* Dots */}
          <div className="flex gap-1.5">
            {dimensions.map((_, i) => (
              <button
                key={i}
                onClick={() => setStep(i)}
                className={`w-2 h-2 rounded-full transition-colors ${i === step ? "bg-primary" : i < step ? "bg-sage-medium" : "bg-muted"}`}
              />
            ))}
          </div>

          {isLast ? (
            <Button onClick={handleSubmit} disabled={isSubmitting} className="gap-2">
              {isSubmitting ? "Saving..." : <><Check className="h-4 w-4" /> Submit</>}
            </Button>
          ) : (
            <Button onClick={() => setStep((s) => s + 1)} className="gap-2">
              Next <ArrowRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

const Nav = ({ navigate }: { navigate: (path: string) => void }) => (
  <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
    <div className="container mx-auto flex items-center justify-between py-4 px-6">
      <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate("/")}>
        <Leaf className="h-6 w-6 text-primary" />
        <span className="font-display text-xl text-foreground">Ember</span>
      </div>
      <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard")}>
        Dashboard
      </Button>
    </div>
  </nav>
);

export default CheckIn;
