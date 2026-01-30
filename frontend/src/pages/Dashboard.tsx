import { useEffect, useState } from "react";
import { dashboardService, authService, DashboardSummary, TrendData } from "../lib/api";
import { generateSimulationData, calculateCareScore, AnalysisResult, HealthMetric } from "../lib/simulation";
import { Card, CardHeader, CardTitle, CardValue } from "../components/ui/Card";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { Activity, ShieldCheck, TrendingUp, AlertCircle, ArrowRight, RefreshCw, Cloud } from "lucide-react";
import { clsx } from "clsx";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/Button";

interface DisplayData {
  date: string;
  heartRate: number;
  hrv?: number;
  sleepDuration?: number;
  activityLevel?: number;
}

export const Dashboard = () => {
  const [data, setData] = useState<DisplayData[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUsingRealData, setIsUsingRealData] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const userId = authService.getUserId();

  useEffect(() => {
    loadDashboardData();
  }, [userId]);

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (userId) {
        // Try to fetch real data from API
        const [summaryData, trendsData] = await Promise.all([
          dashboardService.getSummary(userId).catch(() => null),
          dashboardService.getTrends(userId, 60).catch(() => null)
        ]);

        if (summaryData && summaryData.care_score) {
          setSummary(summaryData);
          setIsUsingRealData(true);

          // Convert trends to display format
          if (trendsData && trendsData.trends.length > 0) {
            const displayData = trendsData.trends.map((t: TrendData) => ({
              date: t.date,
              heartRate: t.heart_rate || 70,
              hrv: t.hrv || 65,
              sleepDuration: t.sleep_duration || 7.5,
              activityLevel: t.activity_level || 8000
            }));
            setData(displayData);
          } else {
            // Use simulation data for charts if no trend data
            setData(generateSimulationData().map(d => ({
              date: d.date,
              heartRate: d.heartRate,
              hrv: d.hrv,
              sleepDuration: d.sleepDuration,
              activityLevel: d.activityLevel
            })));
          }

          // Convert API care_score to analysis format
          const careScore = summaryData.care_score;
          setAnalysis({
            currentScore: careScore.score || 0,
            breakdown: {
              severity: careScore.components.severity,
              persistence: careScore.components.persistence,
              crossSignal: careScore.components.cross_signal,
              manualModifier: careScore.components.manual_modifier,
              total: careScore.score || 0
            },
            status: careScore.status as AnalysisResult["status"],
            driftDetected: (careScore.drift_score || 0) > 30,
            confidence: careScore.confidence || 85,
            stability: careScore.stability || (100 - (careScore.score || 0)),
            trends: []
          });
        } else {
          // Fall back to simulation data
          loadSimulationData();
        }
      } else {
        // No user, use simulation data
        loadSimulationData();
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      loadSimulationData();
    } finally {
      setIsLoading(false);
    }
  };

  const loadSimulationData = () => {
    setIsUsingRealData(false);
    const simData = generateSimulationData();
    setData(simData.map(d => ({
      date: d.date,
      heartRate: d.heartRate,
      hrv: d.hrv,
      sleepDuration: d.sleepDuration,
      activityLevel: d.activityLevel
    })));
    const latest = simData[simData.length - 1];
    const result = calculateCareScore(latest);
    result.trends = simData;
    setAnalysis(result);
  };

  if (isLoading || !analysis) {
    return (
      <div className="p-12 text-center text-gray-400 flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin" />
        Initializing Pulse AI Kernel...
      </div>
    );
  }

  const scoreColor =
    analysis.currentScore > 70 ? "text-red-600" :
      analysis.currentScore > 50 ? "text-amber-600" :
        analysis.currentScore > 30 ? "text-blue-600" : "text-emerald-600";

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Clinical Surveillance</h1>
          <p className="text-gray-500 mt-1">Real-time monitoring and drift detection.</p>
        </div>
        <div className="flex items-center gap-4">
          {/* Data Source Indicator */}
          <div className={clsx(
            "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium",
            isUsingRealData
              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
              : "bg-amber-50 text-amber-700 border border-amber-200"
          )}>
            {isUsingRealData ? (
              <>
                <Cloud className="w-3.5 h-3.5" />
                Live Data
              </>
            ) : (
              <>
                <Activity className="w-3.5 h-3.5" />
                Demo Mode
              </>
            )}
          </div>

          {/* System Status */}
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span className="text-sm font-medium text-gray-600">System Active</span>
          </div>
        </div>
      </div>

      {/* No data warning with sync button */}
      {!isUsingRealData && userId && (
        <div className="flex items-center justify-between p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600" />
            <p className="text-sm text-amber-800">
              Showing simulated data. Sync your health data to see real insights.
            </p>
          </div>
          <Link to="/sync">
            <Button variant="outline" className="gap-2 text-sm">
              <RefreshCw className="w-4 h-4" /> Sync Data
            </Button>
          </Link>
        </div>
      )}

      {/* Hero Score Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1 border-l-4 border-l-gray-900">
          <CardHeader className="flex items-center justify-between">
            <CardTitle>CareScore™</CardTitle>
            <Activity className="w-5 h-5 text-gray-400" />
          </CardHeader>
          <div className="flex items-baseline gap-2">
            <span className={clsx("text-6xl font-bold tracking-tighter", scoreColor)}>
              {analysis.currentScore}
            </span>
            <span className="text-gray-400 font-medium">/ 100</span>
          </div>
          <div className="mt-4 flex items-center gap-2">
            <span className={clsx(
              "px-2.5 py-0.5 rounded-full text-xs font-medium border",
              analysis.status === "High" ? "bg-red-50 text-red-700 border-red-200" :
                analysis.status === "Moderate" ? "bg-amber-50 text-amber-700 border-amber-200" :
                  analysis.status === "Mild" ? "bg-blue-50 text-blue-700 border-blue-200" :
                    "bg-emerald-50 text-emerald-700 border-emerald-200"
            )}>
              {analysis.status} Risk
            </span>
            {analysis.driftDetected && (
              <span className="text-xs text-gray-500">Clinical drift detected</span>
            )}
          </div>

          {analysis.currentScore > 70 && (
            <div className="mt-6">
              <Link to="/escalation">
                <Button variant="danger" className="w-full gap-2">
                  Review Escalation <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
          )}
        </Card>

        <Card className="lg:col-span-2" delay={0.1}>
          <CardHeader>
            <CardTitle>60-Day Drift Analysis</CardTitle>
          </CardHeader>
          <div className="h-[200px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorHr" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#111827" stopOpacity={0.1} />
                    <stop offset="95%" stopColor="#111827" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  hide
                />
                <YAxis hide domain={['dataMin - 10', 'dataMax + 10']} />
                <Tooltip
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <ReferenceLine y={70} stroke="#E5E7EB" strokeDasharray="3 3" />
                <Area
                  type="monotone"
                  dataKey="heartRate"
                  stroke="#111827"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorHr)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-between text-xs text-gray-400 mt-2 px-2">
            <span>60 Days Ago</span>
            <span>Today</span>
          </div>
        </Card>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card delay={0.2}>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Confidence</CardTitle>
            <ShieldCheck className="w-4 h-4 text-gray-400" />
          </CardHeader>
          <CardValue>{analysis.confidence.toFixed(1)}%</CardValue>
          <p className="text-xs text-gray-500 mt-2">AI Model Certainty</p>
        </Card>

        <Card delay={0.3}>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Stability</CardTitle>
            <TrendingUp className="w-4 h-4 text-gray-400" />
          </CardHeader>
          <CardValue>{analysis.stability.toFixed(0)}/100</CardValue>
          <p className="text-xs text-gray-500 mt-2">Inverse Volatility Index</p>
        </Card>

        <Card delay={0.4}>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Drift Factors</CardTitle>
            <AlertCircle className="w-4 h-4 text-gray-400" />
          </CardHeader>
          <div className="space-y-2">
            {analysis.breakdown.severity > 20 && (
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                High Severity Deviation
              </div>
            )}
            {analysis.breakdown.persistence > 10 && (
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                Sustained Trend (&gt;14 days)
              </div>
            )}
            {analysis.breakdown.manualModifier > 0 && (
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                Reported Symptoms
              </div>
            )}
            {analysis.currentScore < 30 && (
              <div className="text-sm text-gray-500">No significant drift factors.</div>
            )}
          </div>
        </Card>
      </div>

      {/* Current Metrics from API */}
      {summary?.current_metrics && (
        <Card delay={0.5}>
          <CardHeader>
            <CardTitle>Current Vitals</CardTitle>
          </CardHeader>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {summary.current_metrics.heart_rate.value && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500">Heart Rate</p>
                <p className="text-xl font-semibold text-gray-900">
                  {summary.current_metrics.heart_rate.value.toFixed(0)}
                  <span className="text-sm font-normal text-gray-400 ml-1">bpm</span>
                </p>
              </div>
            )}
            {summary.current_metrics.hrv.value && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500">HRV</p>
                <p className="text-xl font-semibold text-gray-900">
                  {summary.current_metrics.hrv.value.toFixed(0)}
                  <span className="text-sm font-normal text-gray-400 ml-1">ms</span>
                </p>
              </div>
            )}
            {summary.current_metrics.sleep_duration.value && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500">Sleep</p>
                <p className="text-xl font-semibold text-gray-900">
                  {summary.current_metrics.sleep_duration.value.toFixed(1)}
                  <span className="text-sm font-normal text-gray-400 ml-1">hrs</span>
                </p>
              </div>
            )}
            {summary.current_metrics.activity_level.value && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500">Steps</p>
                <p className="text-xl font-semibold text-gray-900">
                  {summary.current_metrics.activity_level.value.toLocaleString()}
                </p>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};
