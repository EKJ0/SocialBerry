import { motion } from "framer-motion";
import { Heart, Shield, TrendingUp, Users, ArrowRight, Leaf, Bell, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import heroImage from "@/assets/hero-illustration.jpg";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.15, duration: 0.6, ease: "easeOut" as const },
  }),
};

const features = [
  {
    icon: BarChart3,
    title: "60-Second Check-ins",
    description: "Quick daily questions about energy, sleep, stress, and motivation. Under a minute to understand your emotional state.",
  },
  {
    icon: TrendingUp,
    title: "Burnout Risk Tracking",
    description: "See your burnout percentage trend over time. Spot patterns before they become problems.",
  },
  {
    icon: Users,
    title: "Trusted Safety Net",
    description: "Choose 1–3 people you trust. If your burnout crosses your threshold, they're quietly notified.",
  },
  {
    icon: Bell,
    title: "Early Warnings",
    description: "The app detects sustained overload — not just a bad day. You get support suggestions before crisis hits.",
  },
];

const steps = [
  { number: "01", title: "Check in daily", description: "Answer quick questions about how you're feeling. Takes under a minute." },
  { number: "02", title: "Track your trends", description: "Watch your burnout risk over time. Notice patterns and triggers." },
  { number: "03", title: "Get early warnings", description: "The app notices when your overload is sustained, not just a bad day." },
  { number: "04", title: "Activate your safety net", description: "Your trusted people are quietly notified so someone can check in." },
];

const LandingPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="container mx-auto flex items-center justify-between py-4 px-6">
          <div className="flex items-center gap-2">
            <Leaf className="h-6 w-6 text-primary" />
            <span className="font-display text-xl text-foreground">Ember</span>
          </div>
          <div className="flex items-center gap-3">
            {user ? (
              <>
                <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard")}>Dashboard</Button>
              </>
            ) : (
              <>
                <Button variant="ghost" size="sm" onClick={() => navigate("/login")}>Sign In</Button>
                <Button size="sm" onClick={() => navigate("/signup")}>Get Started</Button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="gradient-hero pt-32 pb-20 px-6">
        <div className="container mx-auto grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial="hidden"
            animate="visible"
            className="space-y-6"
          >
            <motion.p variants={fadeUp} custom={0} className="text-primary font-semibold tracking-wide uppercase text-sm">
              Burnout Early Warning System
            </motion.p>
            <motion.h1 variants={fadeUp} custom={1} className="text-4xl md:text-5xl lg:text-6xl font-display text-foreground leading-tight">
              Notice burnout before it breaks you
            </motion.h1>
            <motion.p variants={fadeUp} custom={2} className="text-lg text-muted-foreground max-w-lg leading-relaxed">
              Daily check-ins that track your emotional state. If your burnout rises too high, someone you trust is quietly notified — so you never have to face it alone.
            </motion.p>
            <motion.div variants={fadeUp} custom={3} className="flex flex-wrap gap-4 pt-2">
              <Button size="lg" onClick={() => navigate(user ? "/dashboard" : "/signup")} className="gap-2">
                Start Tracking <ArrowRight className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="lg" onClick={() => document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" })}>
                How It Works
              </Button>
            </motion.div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="hidden lg:block"
          >
            <img src={heroImage} alt="Gentle protective illustration representing emotional safety" className="w-full max-w-lg mx-auto rounded-2xl shadow-xl" />
          </motion.div>
        </div>
      </section>

      {/* Key Moments */}
      <section className="py-20 px-6 bg-card">
        <div className="container mx-auto text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-display text-foreground mb-4">The moments that matter</h2>
          <p className="text-muted-foreground max-w-xl mx-auto">Three powerful realizations that change everything about how you handle stress.</p>
        </div>
        <div className="container mx-auto grid md:grid-cols-3 gap-8">
          {[
            { icon: Heart, quote: "My burnout is rising and I didn't realize it.", color: "text-coral" },
            { icon: Shield, quote: "I don't have to explain everything for someone to know I'm struggling.", color: "text-primary" },
            { icon: Users, quote: "Someone checked in before I broke down.", color: "text-forest" },
          ].map((moment, i) => (
            <motion.div
              key={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              variants={fadeUp}
              custom={i}
              className="bg-background rounded-2xl p-8 border border-border hover:shadow-lg transition-shadow"
            >
              <moment.icon className={`h-8 w-8 ${moment.color} mb-4`} />
              <p className="font-display text-xl text-foreground italic leading-relaxed">"{moment.quote}"</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6">
        <div className="container mx-auto text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-display text-foreground mb-4">Built for your emotional safety</h2>
          <p className="text-muted-foreground max-w-xl mx-auto">Low-pressure, private, and designed to help before crisis hits.</p>
        </div>
        <div className="container mx-auto grid md:grid-cols-2 gap-8 max-w-4xl">
          {features.map((feature, i) => (
            <motion.div
              key={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              variants={fadeUp}
              custom={i}
              className="flex gap-5 p-6 rounded-2xl bg-card border border-border hover:border-primary/30 transition-colors"
            >
              <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-sage-light flex items-center justify-center">
                <feature.icon className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-display text-xl text-foreground mb-1">{feature.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{feature.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-6 gradient-sage">
        <div className="container mx-auto text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-display text-foreground mb-4">How Ember works</h2>
          <p className="text-muted-foreground max-w-xl mx-auto">Four simple steps to build your emotional safety net.</p>
        </div>
        <div className="container mx-auto grid md:grid-cols-4 gap-6 max-w-5xl">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              variants={fadeUp}
              custom={i}
              className="text-center"
            >
              <div className="text-5xl font-display text-primary/20 mb-3">{step.number}</div>
              <h3 className="font-display text-lg text-foreground mb-2">{step.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{step.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 gradient-warm">
        <div className="container mx-auto text-center max-w-2xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }}>
            <motion.h2 variants={fadeUp} custom={0} className="text-3xl md:text-4xl font-display text-foreground mb-4">
              You don't have to explain everything to be supported
            </motion.h2>
            <motion.p variants={fadeUp} custom={1} className="text-muted-foreground mb-8 text-lg">
              Start tracking your emotional state today. Build a safety net of people who care.
            </motion.p>
            <motion.div variants={fadeUp} custom={2}>
              <Button size="lg" onClick={() => navigate(user ? "/dashboard" : "/signup")} className="gap-2">
                Start Your Journey <ArrowRight className="h-4 w-4" />
              </Button>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-border">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Leaf className="h-5 w-5 text-primary" />
            <span className="font-display text-foreground">Ember</span>
          </div>
          <p className="text-sm text-muted-foreground">Your emotional safety net</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
