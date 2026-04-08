import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Leaf, Users, Plus, Trash2, Mail, Shield, AlertTriangle, ChevronRight, X, UserCheck, Clock, UserX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import { z } from "zod";

const contactSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(100, "Name must be under 100 characters"),
  email: z.string().trim().email("Please enter a valid email").max(255, "Email must be under 255 characters"),
  relationship: z.string().min(1, "Please select a relationship"),
  alert_threshold: z.number().min(30).max(100),
});

const relationships = [
  { value: "partner", label: "Partner", icon: "💕" },
  { value: "family", label: "Family", icon: "👨‍👩‍👧" },
  { value: "friend", label: "Friend", icon: "🤝" },
  { value: "counselor", label: "Counselor", icon: "🩺" },
];

const statusConfig = {
  pending: { label: "Pending", icon: Clock, className: "bg-warning/10 text-warning-foreground" },
  accepted: { label: "Active", icon: UserCheck, className: "bg-sage-light text-primary" },
  declined: { label: "Declined", icon: UserX, className: "bg-destructive/10 text-destructive" },
};

const TrustedContacts = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [formData, setFormData] = useState({ name: "", email: "", relationship: "friend", alert_threshold: 75 });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const { data: contacts = [], isLoading } = useQuery({
    queryKey: ["trusted-contacts"],
    queryFn: async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return [];
      const { data, error } = await supabase
        .from("trusted_contacts")
        .select("*")
        .order("created_at", { ascending: false });
      if (error) throw error;
      return data;
    },
  });

  const addContact = useMutation({
    mutationFn: async (contact: typeof formData) => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("You must be signed in to add contacts");
      const { error } = await supabase.from("trusted_contacts").insert({
        user_id: user.id,
        name: contact.name.trim(),
        email: contact.email.trim(),
        relationship: contact.relationship,
        alert_threshold: contact.alert_threshold,
      });
      if (error) throw error;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trusted-contacts"] });
      setShowInviteForm(false);
      setFormData({ name: "", email: "", relationship: "friend", alert_threshold: 75 });
      setFormErrors({});
      toast.success("Invitation sent! They'll be notified about their role.");
    },
    onError: (err) => toast.error(err.message),
  });

  const removeContact = useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase.from("trusted_contacts").delete().eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trusted-contacts"] });
      toast.success("Contact removed from your safety net.");
    },
    onError: (err) => toast.error(err.message),
  });

  const updateThreshold = useMutation({
    mutationFn: async ({ id, threshold }: { id: string; threshold: number }) => {
      const { error } = await supabase.from("trusted_contacts").update({ alert_threshold: threshold }).eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trusted-contacts"] });
      toast.success("Alert threshold updated.");
    },
  });

  const handleSubmit = () => {
    const result = contactSchema.safeParse(formData);
    if (!result.success) {
      const errors: Record<string, string> = {};
      result.error.errors.forEach((e) => { errors[e.path[0] as string] = e.message; });
      setFormErrors(errors);
      return;
    }
    if (contacts.length >= 3) {
      toast.error("You can have up to 3 trusted contacts.");
      return;
    }
    setFormErrors({});
    addContact.mutate(formData);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="container mx-auto flex items-center justify-between py-4 px-6">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate("/")}>
            <Leaf className="h-6 w-6 text-primary" />
            <span className="font-display text-xl text-foreground">Ember</span>
          </div>
          <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard")}>Dashboard</Button>
        </div>
      </nav>

      <div className="pt-24 pb-12 px-6">
        <div className="container mx-auto max-w-3xl">
          {/* Header */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-sage-light flex items-center justify-center">
                <Shield className="h-5 w-5 text-primary" />
              </div>
              <h1 className="text-3xl font-display text-foreground">Your Safety Net</h1>
            </div>
            <p className="text-muted-foreground">Choose up to 3 people you trust. If your burnout risk crosses a threshold, they'll be gently notified.</p>
          </motion.div>

          {/* Info Banner */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-sage-light rounded-2xl p-5 mb-8 flex items-start gap-3"
          >
            <Users className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
            <div className="text-sm text-foreground">
              <p className="font-medium mb-1">How it works</p>
              <p className="text-muted-foreground">Your trusted contacts are <strong>not</strong> therapists or rescuers — they're safe people who can quietly check in when you're under emotional strain. They'll receive a gentle notification, not detailed data.</p>
            </div>
          </motion.div>

          {/* Contacts List */}
          <div className="space-y-4 mb-6">
            <AnimatePresence>
              {contacts.map((contact, i) => {
                const status = statusConfig[contact.status as keyof typeof statusConfig] || statusConfig.pending;
                const StatusIcon = status.icon;
                return (
                  <motion.div
                    key={contact.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: -100 }}
                    transition={{ delay: i * 0.05 }}
                    className="bg-card rounded-2xl border border-border p-6"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-sage-light flex items-center justify-center text-lg">
                          {relationships.find((r) => r.value === contact.relationship)?.icon || "🤝"}
                        </div>
                        <div>
                          <p className="font-medium text-foreground">{contact.name}</p>
                          <p className="text-sm text-muted-foreground flex items-center gap-1">
                            <Mail className="h-3 w-3" /> {contact.email}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2.5 py-1 rounded-full flex items-center gap-1 ${status.className}`}>
                          <StatusIcon className="h-3 w-3" /> {status.label}
                        </span>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-destructive"
                          onClick={() => removeContact.mutate(contact.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="flex items-center justify-between bg-background rounded-xl p-4 border border-border">
                      <div>
                        <p className="text-sm font-medium text-foreground">Alert Threshold</p>
                        <p className="text-xs text-muted-foreground">Notified when your burnout reaches this level</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <input
                          type="range"
                          min={30}
                          max={100}
                          value={contact.alert_threshold}
                          onChange={(e) => updateThreshold.mutate({ id: contact.id, threshold: parseInt(e.target.value) })}
                          className="w-24 h-2 rounded-full appearance-none cursor-pointer bg-muted accent-primary
                            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
                            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary
                            [&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:rounded-full
                            [&::-moz-range-thumb]:bg-primary"
                        />
                        <span className="text-sm font-semibold text-foreground w-10 text-right">{contact.alert_threshold}%</span>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {isLoading && (
              <div className="text-center py-12 text-muted-foreground">Loading your safety net...</div>
            )}

            {!isLoading && contacts.length === 0 && !showInviteForm && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-12 bg-card rounded-2xl border border-border"
              >
                <Users className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
                <h3 className="font-display text-xl text-foreground mb-2">No trusted contacts yet</h3>
                <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto">
                  Add someone you trust — they'll be gently notified if your burnout risk rises too high.
                </p>
                <Button onClick={() => setShowInviteForm(true)} className="gap-2">
                  <Plus className="h-4 w-4" /> Add Your First Contact
                </Button>
              </motion.div>
            )}
          </div>

          {/* Add Button */}
          {contacts.length > 0 && contacts.length < 3 && !showInviteForm && (
            <Button variant="outline" onClick={() => setShowInviteForm(true)} className="w-full gap-2 mb-6">
              <Plus className="h-4 w-4" /> Add Trusted Contact ({contacts.length}/3)
            </Button>
          )}

          {/* Invite Form */}
          <AnimatePresence>
            {showInviteForm && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="bg-card rounded-2xl border border-border p-8 mb-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="font-display text-xl text-foreground">Invite a Trusted Person</h2>
                    <Button variant="ghost" size="icon" onClick={() => { setShowInviteForm(false); setFormErrors({}); }}>
                      <X className="h-4 w-4" />
                    </Button>
                  </div>

                  <div className="space-y-5">
                    <div>
                      <Label className="text-sm font-medium text-foreground">Their Name</Label>
                      <Input
                        placeholder="e.g. Sarah"
                        value={formData.name}
                        onChange={(e) => setFormData((d) => ({ ...d, name: e.target.value }))}
                        className="mt-1.5"
                      />
                      {formErrors.name && <p className="text-xs text-destructive mt-1">{formErrors.name}</p>}
                    </div>

                    <div>
                      <Label className="text-sm font-medium text-foreground">Their Email</Label>
                      <Input
                        type="email"
                        placeholder="e.g. sarah@example.com"
                        value={formData.email}
                        onChange={(e) => setFormData((d) => ({ ...d, email: e.target.value }))}
                        className="mt-1.5"
                      />
                      {formErrors.email && <p className="text-xs text-destructive mt-1">{formErrors.email}</p>}
                    </div>

                    <div>
                      <Label className="text-sm font-medium text-foreground">Relationship</Label>
                      <div className="grid grid-cols-2 gap-2 mt-1.5">
                        {relationships.map((rel) => (
                          <button
                            key={rel.value}
                            onClick={() => setFormData((d) => ({ ...d, relationship: rel.value }))}
                            className={`flex items-center gap-2 p-3 rounded-xl border text-sm transition-colors ${
                              formData.relationship === rel.value
                                ? "border-primary bg-sage-light text-foreground"
                                : "border-border bg-background text-muted-foreground hover:border-primary/30"
                            }`}
                          >
                            <span>{rel.icon}</span>
                            <span>{rel.label}</span>
                          </button>
                        ))}
                      </div>
                      {formErrors.relationship && <p className="text-xs text-destructive mt-1">{formErrors.relationship}</p>}
                    </div>

                    <div>
                      <Label className="text-sm font-medium text-foreground">Alert Threshold</Label>
                      <p className="text-xs text-muted-foreground mb-3">They'll be notified when your burnout reaches this percentage.</p>
                      <div className="flex items-center gap-4">
                        <input
                          type="range"
                          min={30}
                          max={100}
                          value={formData.alert_threshold}
                          onChange={(e) => setFormData((d) => ({ ...d, alert_threshold: parseInt(e.target.value) }))}
                          className="flex-1 h-3 rounded-full appearance-none cursor-pointer bg-muted accent-primary
                            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-7 [&::-webkit-slider-thumb]:h-7
                            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:shadow-lg
                            [&::-webkit-slider-thumb]:border-4 [&::-webkit-slider-thumb]:border-background
                            [&::-moz-range-thumb]:w-7 [&::-moz-range-thumb]:h-7 [&::-moz-range-thumb]:rounded-full
                            [&::-moz-range-thumb]:bg-primary [&::-moz-range-thumb]:border-4 [&::-moz-range-thumb]:border-background"
                        />
                        <span className="text-2xl font-display text-foreground w-16 text-right">{formData.alert_threshold}%</span>
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground mt-1">
                        <span>More sensitive (30%)</span>
                        <span>Only critical (100%)</span>
                      </div>
                    </div>

                    {/* What They'll See */}
                    <div className="bg-background rounded-xl border border-border p-4">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">What they'll receive</p>
                      <div className="bg-card rounded-lg border border-border p-4">
                        <p className="text-sm text-foreground italic">
                          "Someone you care about may be under increasing emotional strain right now. Consider checking in with them."
                        </p>
                      </div>
                      <p className="text-xs text-muted-foreground mt-2">They won't see your data, scores, or details — just a gentle prompt.</p>
                    </div>

                    <Button onClick={handleSubmit} disabled={addContact.isPending} className="w-full gap-2">
                      {addContact.isPending ? "Sending..." : <><Mail className="h-4 w-4" /> Send Invitation</>}
                    </Button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default TrustedContacts;
