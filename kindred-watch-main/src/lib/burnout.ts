/**
 * Calculate burnout risk score from check-in dimensions.
 * 
 * Positive dimensions (higher = better): energy, sleep, motivation, focus
 * Negative dimensions (higher = worse): overwhelm, withdrawal
 * 
 * Returns 0–100 where 100 = maximum burnout risk.
 */
export function calculateBurnoutScore(values: {
  energy: number;
  sleep: number;
  overwhelm: number;
  motivation: number;
  focus: number;
  withdrawal: number;
}): number {
  // Invert positive dimensions (high energy = low burnout contribution)
  const energyRisk = 11 - values.energy;       // 1-10 → 10-1
  const sleepRisk = 11 - values.sleep;
  const motivationRisk = 11 - values.motivation;
  const focusRisk = 11 - values.focus;

  // Negative dimensions used directly (high overwhelm = high burnout)
  const overwhelmRisk = values.overwhelm;
  const withdrawalRisk = values.withdrawal;

  // Weighted average — overwhelm and withdrawal weighted slightly higher
  const weighted =
    energyRisk * 1.0 +
    sleepRisk * 1.0 +
    overwhelmRisk * 1.3 +
    motivationRisk * 1.0 +
    focusRisk * 0.8 +
    withdrawalRisk * 1.2;

  const maxWeighted = 10 * (1.0 + 1.0 + 1.3 + 1.0 + 0.8 + 1.2); // 63.0
  const score = Math.round((weighted / maxWeighted) * 100);

  return Math.max(0, Math.min(100, score));
}

/**
 * Get risk level label and color info from a burnout score
 */
export function getRiskInfo(score: number) {
  if (score < 30) return { label: "Low", level: "low" as const };
  if (score < 50) return { label: "Moderate", level: "moderate" as const };
  if (score < 70) return { label: "Elevated", level: "elevated" as const };
  if (score < 85) return { label: "High", level: "high" as const };
  return { label: "Critical", level: "critical" as const };
}
