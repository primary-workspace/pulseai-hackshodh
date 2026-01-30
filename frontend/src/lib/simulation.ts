/**
 * PULSE AI SIMULATION ENGINE
 * Simulates backend logic for data generation and CareScore calculation.
 */

import { addDays, subDays, format } from "date-fns";

export interface HealthMetric {
  date: string;
  heartRate: number; // bpm
  hrv: number; // ms
  sleepDuration: number; // hours
  activityLevel: number; // steps
  breathingRate: number; // brpm
  systolicBP: number; // mmHg
  diastolicBP: number; // mmHg
  bloodSugar: number; // mg/dL
  symptoms: string[];
}

export interface CareScoreBreakdown {
  severity: number; // 0-40
  persistence: number; // 0-25
  crossSignal: number; // 0-20
  manualModifier: number; // 0-15
  total: number; // 0-100
}

export interface AnalysisResult {
  currentScore: number;
  breakdown: CareScoreBreakdown;
  status: "Stable" | "Mild" | "Moderate" | "High";
  driftDetected: boolean;
  confidence: number;
  stability: number;
  trends: HealthMetric[];
}

// Baseline values for a healthy individual
const BASELINE = {
  heartRate: 70,
  hrv: 65,
  sleepDuration: 7.5,
  breathingRate: 14,
  systolicBP: 120,
  diastolicBP: 80,
  bloodSugar: 90,
};

// Generate 60 days of data with a gradual clinical drift
export const generateSimulationData = (): HealthMetric[] => {
  const data: HealthMetric[] = [];
  const days = 60;
  
  for (let i = 0; i < days; i++) {
    const date = subDays(new Date(), days - 1 - i);
    
    // Introduce drift starting from day 30
    const driftFactor = i > 30 ? (i - 30) / 30 : 0; 
    
    // Random noise
    const noise = (scale: number) => (Math.random() - 0.5) * scale;

    data.push({
      date: format(date, "yyyy-MM-dd"),
      heartRate: BASELINE.heartRate + (driftFactor * 15) + noise(5), // Drift up
      hrv: BASELINE.hrv - (driftFactor * 20) + noise(10), // Drift down (bad)
      sleepDuration: Math.max(4, BASELINE.sleepDuration - (driftFactor * 2) + noise(1)), // Drift down
      activityLevel: 8000 - (driftFactor * 3000) + noise(2000),
      breathingRate: BASELINE.breathingRate + (driftFactor * 4) + noise(2),
      systolicBP: BASELINE.systolicBP + (driftFactor * 10) + noise(5),
      diastolicBP: BASELINE.diastolicBP + (driftFactor * 5) + noise(5),
      bloodSugar: BASELINE.bloodSugar + (driftFactor * 15) + noise(10),
      symptoms: i > 45 ? ["Fatigue", "Mild Dizziness"] : [],
    });
  }
  return data;
};

// Calculate CareScore based on the latest data point vs baseline
export const calculateCareScore = (metric: HealthMetric): AnalysisResult => {
  // 1. Severity Score (0-40)
  // Calculate Z-score like deviations (simplified for simulation)
  const hrDev = Math.max(0, (metric.heartRate - BASELINE.heartRate) / 10); // +10bpm = 1 unit
  const hrvDev = Math.max(0, (BASELINE.hrv - metric.hrv) / 10); // -10ms = 1 unit
  const sleepDev = Math.max(0, (BASELINE.sleepDuration - metric.sleepDuration)); // -1hr = 1 unit
  
  let severity = (hrDev + hrvDev + sleepDev) * 5;
  severity = Math.min(40, severity);

  // 2. Persistence Score (0-25)
  // In a real system, we'd look back X days. Here we simulate it based on severity magnitude assuming it's been building up.
  const persistence = Math.min(25, severity * 0.6);

  // 3. Cross-Signal Validation (0-20)
  let signals = 0;
  if (metric.heartRate > BASELINE.heartRate + 5) signals++;
  if (metric.hrv < BASELINE.hrv - 5) signals++;
  if (metric.sleepDuration < BASELINE.sleepDuration - 1) signals++;
  if (metric.breathingRate > BASELINE.breathingRate + 2) signals++;
  
  const crossSignal = Math.min(20, signals * 5);

  // 4. Manual Modifier (0-15)
  let manual = 0;
  if (metric.systolicBP > 130) manual += 5;
  if (metric.bloodSugar > 110) manual += 5;
  if (metric.symptoms.length > 0) manual += 5;
  manual = Math.min(15, manual);

  const totalScore = Math.round(severity + persistence + crossSignal + manual);

  let status: AnalysisResult["status"] = "Stable";
  if (totalScore > 30) status = "Mild";
  if (totalScore > 50) status = "Moderate";
  if (totalScore > 70) status = "High";

  return {
    currentScore: totalScore,
    breakdown: { severity, persistence, crossSignal, manualModifier: manual, total: totalScore },
    status,
    driftDetected: totalScore > 30,
    confidence: 85 + (Math.random() * 10), // Mock confidence
    stability: Math.max(0, 100 - totalScore), // Inverse of risk
    trends: [], // Populated by caller
  };
};
