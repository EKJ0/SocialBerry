import { useMemo } from "react";
import { motion } from "framer-motion";
import { Leaf, TrendingUp, TrendingDown, Minus, Users, Moon, Zap, Brain, Heart, Eye, UserMinus, AlertTriangle, ChevronRight, LogOut } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { Area, AreaChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";
import { format, subDays } from "date-fns";

const dimensionMeta = [
  { key: "energy", label: "Energy", icon: Zap, color: "text-primary" },
  { key: "sleep", label: "Sleep", icon: Moon, color: "text-sage-medium" },
  { key: "overwhelm", label: "Overwhelm", icon: Brain, color: "text-coral" },
  { key: "motivation", label: "Motivation", icon: Heart, color: "text-primary" },
  { key: "focus", label: "Focus", icon: Eye, color: "text-sage-medium" },
  { key: "withdrawal", label: "Withdrawal", icon: UserMinus, color: "text-coral" },
];

const getRiskColor = (risk: number) => {
  if (risk < 40) return "text-primary";
  if (risk < 65) return "text-warning";
  return "text-coral";
};

const getRiskBg = (risk: number) => {
  if (risk < 40) return "stroke-primary";
  if (risk < 65) return "stroke-warning";
  return "stroke-coral";
};

const getRiskLabel = (risk: number) => {
  if (risk < 30) return "Low";
  if (risk < 50) return "Moderate";
  if (risk < 70) return "Elevated";
  if (risk < 85) return "High";
  return "Critical";
};

const BurnoutGauge = ({ risk }: { risk: number }) => {
  const circumference = 2 * Math.PI * 80;
  const offset = circumference - (risk / 100) * circumference;

  return (
    <div className="relative w-52 h-52 mx-auto">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 200 200">
        <circle cx="100" cy="100" r="80" fill="none" stroke="hsl(var(--border))" strokeWidth="12" />
        <motion.circle
          cx="100" cy="100" r="80" fill="none"
          className={getRiskBg(risk)}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: "easeOut" as const }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          className={`text-5xl font-display ${getRiskColor(risk)}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {risk}%
        </motion.span>
        <span className="text-sm text-muted-foreground mt-1">{getRiskLabel(risk)} Risk</span>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();

  // Fetch last 14 days of check-ins
  const { data: checkIns = [] } = useQuery({
    queryKey: ["check-ins", user?.id],
    queryFn: async () => {
      if (!user) return [];
      const since = subDays(new Date(), 14).toISOString().split("T")[0];
      const { data, error } = await supabase
        .from("check_ins")
        .select("*")
        .gte("checked_in_at", since)
        .order("checked_in_at", { ascending: true });
      if (error) throw error;
      return data;
    },
    enabled: !!user,
  });

  // Fetch trusted contacts
  const { data: contacts = [] } = useQuery({
    queryKey: ["trusted-contacts-dashboard", user?.id],
    queryFn: async () => {
      if (!user) return [];
      const { data, error } = await supabase
        .from("trusted_contacts")
        .select("*")
        .order("created_at", { ascending: false });
      if (error) throw error;
      return data;
    },
    enabled: !!user,
  });

  // Derived data
  const latestCheckIn = checkIns.length > 0 ? checkIns[checkIns.length - 1] : null;
  const currentRisk = latestCheckIn?.burnout_score ?? 0;
  const hasCheckedInToday = latestCheckIn?.checked_in_at === new Date().toISOString().split("T")[0];

  const trend = useMemo(() => {
    if (checkIns.length < 2) return "stable";
    const recent = checkIns.slice(-3);
    const older = checkIns.slice(-6, -3);
    if (older.length === 0) return "stable";
    const recentAvg = recent.reduce((s, c) => s + c.burnout_score, 0) / recent.length;
    const olderAvg = older.reduce((s, c) => s + c.burnout_score, 0) / older.length;
    if (recentAvg > olderAvg + 5) return "rising";
    if (recentAvg < olderAvg - 5) return "falling";
    return "stable";
  }, [checkIns]);

  const trendMessage = useMemo(() => {
    if (checkIns.length === 0) return "Start checking in daily to see your trends.";
    if (trend === "rising") return "Your emotional load has been increasing recently.";
    if (trend === "falling") return "You're showing signs of recovery. Keep it up!";
    return "Your emotional state has been relatively stable.";
  }, [checkIns, trend]);

  // Chart data — last 7 days
  const chartData = useMemo(() => {
    const days = [];
    for (let i = 6; i >= 0; i--) {
      const date = subDays(new Date(), i);
      const dateStr = date.toISOString().split("T")[0];
      const checkIn = checkIns.find((c) => c.checked_in_at === dateStr);
      days.push({
        day: format(date, "EEE"),
        risk: checkIn?.burnout_score ?? null,
      });
    }
    return days;
  }, [checkIns]);

  // Today's dimension values for the check-in card
  const todayDimensions = useMemo(() => {
    if (!latestCheckIn || !hasCheckedInToday) return null;
    return dimensionMeta.map((d) => ({
      ...d,
      value: (latestCheckIn as unknown as Record<string, number>)[d.key] ?? 0,
    }));
  }, [latestCheckIn, hasCheckedInToday]);

  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="container mx-auto flex items-center justify-between py-4 px-6">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate("/")}>
            <Leaf className="h-6 w-6 text-primary" />
            <span className="font-display text-xl text-foreground">Ember</span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => navigate("/")}>Home</Button>
            <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground" onClick={signOut}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </nav>

      <div className="pt-24 pb-12 px-6">
        <div className="container mx-auto max-w-5xl">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <h1 className="text-3xl font-display text-foreground">Your Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              {checkIns.length === 0
                ? "Complete your first check-in to start tracking"
                : `${checkIns.length} check-in${checkIns.length !== 1 ? "s" : ""} recorded`}
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Burnout Gauge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="lg:col-span-1 bg-card rounded-2xl border border-border p-8"
            >
              <h2 className="font-display text-xl text-foreground mb-6 text-center">Burnout Risk</h2>
              {checkIns.length > 0 ? (
                <>
                  <BurnoutGauge risk={currentRisk} />
                  <div className="flex items-center justify-center gap-2 mt-6">
                    {trend === "rising" ? (
                      <>
                        <TrendingUp className="h-4 w-4 text-coral" />
                        <span className="text-sm text-coral font-medium">Rising</span>
                      </>
                    ) : trend === "falling" ? (
                      <>
                        <TrendingDown className="h-4 w-4 text-primary" />
                        <span className="text-sm text-primary font-medium">Improving</span>
                      </>
                    ) : (
                      <>
                        <Minus className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground font-medium">Stable</span>
                      </>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground text-sm mb-4">No data yet</p>
                  <Button size="sm" onClick={() => navigate("/check-in")}>First Check-in</Button>
                </div>
              )}
            </motion.div>

            {/* Trend Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="lg:col-span-2 bg-card rounded-2xl border border-border p-8"
            >
              <h2 className="font-display text-xl text-foreground mb-2">Weekly Trend</h2>
              <p className="text-sm text-muted-foreground mb-6">{trendMessage}</p>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(12, 70%, 65%)" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="hsl(12, 70%, 65%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "hsl(150, 10%, 45%)" }} />
                  <YAxis domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "hsl(150, 10%, 45%)" }} />
                  <Tooltip
                    contentStyle={{ background: "hsl(40, 30%, 95%)", border: "1px solid hsl(40, 18%, 86%)", borderRadius: "12px", fontSize: 13 }}
                    formatter={(value: number | null) => [value !== null ? `${value}%` : "No data", "Burnout Risk"]}
                  />
                  <Area type="monotone" dataKey="risk" stroke="hsl(12, 70%, 65%)" strokeWidth={2.5} fill="url(#riskGradient)" connectNulls />
                </AreaChart>
              </ResponsiveContainer>
            </motion.div>

            {/* Daily Check-in */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="lg:col-span-2 bg-card rounded-2xl border border-border p-8"
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="font-display text-xl text-foreground">Today's Check-in</h2>
                  <p className="text-sm text-muted-foreground">
                    {hasCheckedInToday ? "Completed ✓" : "Not yet completed"}
                  </p>
                </div>
                <Button size="sm" onClick={() => navigate("/check-in")} disabled={hasCheckedInToday}>
                  {hasCheckedInToday ? "Done for today" : "Start Check-in"}
                </Button>
              </div>
              {todayDimensions ? (
                <div className="grid sm:grid-cols-3 gap-3">
                  {todayDimensions.map((item) => (
                    <div key={item.key} className="flex items-center gap-3 bg-background rounded-xl p-3 border border-border">
                      <item.icon className={`h-4 w-4 ${item.color} flex-shrink-0`} />
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-medium text-foreground">{item.label}</span>
                          <span className="text-xs font-semibold text-foreground">{item.value}/10</span>
                        </div>
                        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                          <motion.div
                            className="h-full rounded-full bg-primary"
                            initial={{ width: 0 }}
                            animate={{ width: `${item.value * 10}%` }}
                            transition={{ duration: 0.8, delay: 0.5 }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-6">
                  Complete your daily check-in to see your scores here.
                </p>
              )}
            </motion.div>

            {/* Trusted Contacts */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="lg:col-span-1 bg-card rounded-2xl border border-border p-8"
            >
              <div className="flex items-center gap-2 mb-6">
                <Users className="h-5 w-5 text-primary" />
                <h2 className="font-display text-xl text-foreground">Safety Net</h2>
              </div>
              {contacts.length > 0 ? (
                <div className="space-y-3">
                  {contacts.map((person) => (
                    <div key={person.id} className="flex items-center justify-between bg-background rounded-xl p-4 border border-border">
                      <div>
                        <p className="text-sm font-medium text-foreground">{person.name}</p>
                        <p className="text-xs text-muted-foreground capitalize">{person.relationship}</p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${person.status === "accepted" ? "bg-sage-light text-primary" : "bg-muted text-muted-foreground"}`}>
                        {person.status === "accepted" ? "Active" : "Pending"}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">No trusted contacts yet</p>
              )}
              <Button variant="outline" size="sm" className="w-full mt-4" onClick={() => navigate("/trusted-contacts")}>
                Manage Contacts
              </Button>
            </motion.div>

            {/* Alert Banner — only show when risk is elevated */}
            {currentRisk >= 60 && checkIns.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="lg:col-span-3 bg-coral-light rounded-2xl border border-coral/20 p-6 flex items-start gap-4"
              >
                <AlertTriangle className="h-6 w-6 text-coral flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-display text-lg text-foreground">
                    {currentRisk >= 75
                      ? "Your burnout risk is high"
                      : "Your burnout risk has been rising"}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    Consider slowing down or reaching out to someone you trust.
                    {contacts.length > 0 && ` Your safety net will be notified if risk reaches their alert threshold.`}
                  </p>
                </div>
                <Button variant="outline" size="sm" className="flex-shrink-0 gap-1" onClick={() => navigate("/trusted-contacts")}>
                  Get Support <ChevronRight className="h-3 w-3" />
                </Button>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
