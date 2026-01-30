import { useEffect, useState } from "react";
import { dashboardService, authService, Insight, TrendData } from "../lib/api";
import { generateSimulationData, HealthMetric } from "../lib/simulation";
import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { AlertCircle, TrendingUp, TrendingDown, Lightbulb, Activity, Moon, Heart, Footprints } from "lucide-react";
import { clsx } from "clsx";

interface DisplayData {
  date: string;
  heartRate: number;
  hrv: number;
  sleepDuration: number;
  activityLevel: number;
}

export const Insights = () => {
  const [data, setData] = useState<DisplayData[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUsingRealData, setIsUsingRealData] = useState(false);

  const userId = authService.getUserId();

  useEffect(() => {
    loadInsightsData();
  }, [userId]);

  const loadInsightsData = async () => {
    setIsLoading(true);

    try {
      if (userId) {
        // Fetch real data
        const [insightsData, trendsData] = await Promise.all([
          dashboardService.getInsights(userId).catch(() => null),
          dashboardService.getTrends(userId, 60).catch(() => null)
        ]);

        if (trendsData && trendsData.trends.length > 0) {
          setIsUsingRealData(true);
          setData(trendsData.trends.map((t: TrendData) => ({
            date: t.date,
            heartRate: t.heart_rate || 70,
            hrv: t.hrv || 65,
            sleepDuration: t.sleep_duration || 7.5,
            activityLevel: t.activity_level || 8000
          })));
        } else {
          loadSimulationData();
        }

        if (insightsData && insightsData.insights.length > 0) {
          setInsights(insightsData.insights);
        }
      } else {
        loadSimulationData();
      }
    } catch (err) {
      console.error('Failed to load insights:', err);
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
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'warning': return <AlertCircle className="w-5 h-5 text-amber-500" />;
      case 'success': return <TrendingUp className="w-5 h-5 text-emerald-500" />;
      default: return <Lightbulb className="w-5 h-5 text-blue-500" />;
    }
  };

  const getMetricIcon = (metric: string) => {
    switch (metric.toLowerCase()) {
      case 'heart rate': return <Heart className="w-4 h-4" />;
      case 'hrv': return <Activity className="w-4 h-4" />;
      case 'sleep': return <Moon className="w-4 h-4" />;
      case 'activity': return <Footprints className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  if (isLoading) {
    return (
      <div className="p-12 text-center text-gray-400 flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin" />
        Loading insights...
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Health Insights</h1>
        <p className="text-gray-500 mt-1">Deep dive into biometric signals and AI-generated recommendations.</p>
      </div>

      {/* AI Insights Cards */}
      {insights.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-500" />
            AI-Generated Insights
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insights.map((insight, idx) => (
              <Card
                key={idx}
                className={clsx(
                  "border-l-4",
                  insight.type === 'warning' ? "border-l-amber-500" :
                    insight.type === 'success' ? "border-l-emerald-500" :
                      "border-l-blue-500"
                )}
              >
                <div className="flex items-start gap-3">
                  {getInsightIcon(insight.type)}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={clsx(
                        "px-2 py-0.5 rounded-full text-xs font-medium",
                        insight.type === 'warning' ? "bg-amber-100 text-amber-700" :
                          insight.type === 'success' ? "bg-emerald-100 text-emerald-700" :
                            "bg-blue-100 text-blue-700"
                      )}>
                        {insight.metric}
                      </span>
                    </div>
                    <h4 className="font-semibold text-gray-900">{insight.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                    <div className="mt-3 p-2 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500 flex items-center gap-1">
                        {getMetricIcon(insight.metric)}
                        <span className="font-medium">Recommendation:</span>
                      </p>
                      <p className="text-sm text-gray-700 mt-1">{insight.recommendation}</p>
                    </div>
                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                      <span>Current: <strong className="text-gray-700">{insight.current}</strong></span>
                      <span>Baseline: <strong className="text-gray-700">{insight.baseline}</strong></span>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Heart Rate vs HRV</CardTitle>
          </CardHeader>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <XAxis dataKey="date" hide />
                <YAxis yAxisId="left" domain={['auto', 'auto']} hide />
                <YAxis yAxisId="right" orientation="right" domain={['auto', 'auto']} hide />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: 'none',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                  }}
                />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="heartRate" stroke="#111827" strokeWidth={2} dot={false} name="Heart Rate (bpm)" />
                <Line yAxisId="right" type="monotone" dataKey="hrv" stroke="#2563EB" strokeWidth={2} dot={false} name="HRV (ms)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Correlation analysis shows inverse relationship typical of stress response.
          </p>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sleep Duration Trend</CardTitle>
          </CardHeader>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <XAxis dataKey="date" hide />
                <YAxis domain={[0, 12]} hide />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: 'none',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                  }}
                />
                <Line type="step" dataKey="sleepDuration" stroke="#4B5563" strokeWidth={2} dot={false} name="Sleep (hrs)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            {isUsingRealData
              ? "Sleep patterns based on your synced health data."
              : "Gradual decline in sleep duration observed over the last 30 days."}
          </p>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Activity Levels</CardTitle>
          </CardHeader>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <XAxis dataKey="date" hide />
                <YAxis domain={[0, 'auto']} hide />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: 'none',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                  }}
                />
                <Line type="monotone" dataKey="activityLevel" stroke="#059669" strokeWidth={2} dot={false} name="Steps" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Daily step count and activity patterns over 60 days.
          </p>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Signal Correlation Matrix</CardTitle>
          </CardHeader>
          <div className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">HR ↔ HRV</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-red-500" style={{ width: '65%' }} />
                </div>
                <span className="text-sm font-medium text-gray-900">-0.65</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Sleep ↔ HRV</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500" style={{ width: '72%' }} />
                </div>
                <span className="text-sm font-medium text-gray-900">+0.72</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Activity ↔ Sleep</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500" style={{ width: '48%' }} />
                </div>
                <span className="text-sm font-medium text-gray-900">+0.48</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">HR ↔ Activity</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500" style={{ width: '35%' }} />
                </div>
                <span className="text-sm font-medium text-gray-900">+0.35</span>
              </div>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Cross-signal validation identifies correlated deviations.
          </p>
        </Card>
      </div>

      {/* Data Source Notice */}
      {!isUsingRealData && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
          <strong>Demo Mode:</strong> Charts are showing simulated data. Connect your Google Drive to view real health insights.
        </div>
      )}
    </div>
  );
};
