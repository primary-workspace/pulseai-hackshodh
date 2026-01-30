import { useEffect, useState } from "react";
import { AlertTriangle, Phone, Calendar, ArrowRight, CheckCircle2, Clock, XCircle } from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { dashboardService, authService, Escalation as EscalationType } from "../lib/api";
import { clsx } from "clsx";

export const Escalation = () => {
  const [escalations, setEscalations] = useState<EscalationType[]>([]);
  const [activeCount, setActiveCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [dismissing, setDismissing] = useState<number | null>(null);

  const userId = authService.getUserId();

  useEffect(() => {
    loadEscalations();
  }, [userId]);

  const loadEscalations = async () => {
    if (!userId) {
      setIsLoading(false);
      return;
    }

    try {
      const data = await dashboardService.getEscalations(userId, true);
      setEscalations(data.escalations);
      setActiveCount(data.active_count);
    } catch (err) {
      console.error('Failed to load escalations:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAcknowledge = async (escalationId: number, action: string) => {
    setDismissing(escalationId);
    try {
      await dashboardService.acknowledgeEscalation(escalationId, action);
      await loadEscalations();
    } catch (err) {
      console.error('Failed to acknowledge escalation:', err);
    } finally {
      setDismissing(null);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getLevelColor = (level: number) => {
    if (level >= 3) return "red";
    if (level >= 2) return "amber";
    return "blue";
  };

  if (isLoading) {
    return (
      <div className="p-12 text-center text-gray-400 flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin" />
        Loading escalations...
      </div>
    );
  }

  // No escalations view
  if (escalations.length === 0 || activeCount === 0) {
    return (
      <div className="max-w-3xl mx-auto space-y-8">
        <div className="text-center space-y-4 py-12">
          <div className="w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-8 h-8 text-emerald-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">All Clear</h1>
          <p className="text-gray-600 max-w-lg mx-auto">
            No active escalations. Your health metrics are within normal parameters.
            Continue monitoring for sustained health insights.
          </p>
        </div>

        {escalations.length > 0 && (
          <Card>
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-400" />
              Escalation History
            </h3>
            <div className="space-y-3">
              {escalations.filter(e => e.acknowledged).slice(0, 5).map((esc) => (
                <div
                  key={esc.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-gray-300" />
                    <div>
                      <p className="text-sm font-medium text-gray-600 line-through">
                        Level {esc.level} Alert
                      </p>
                      <p className="text-xs text-gray-500">{formatDate(esc.timestamp)}</p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded-full">
                    Resolved
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    );
  }

  // Active escalations view
  const activeEscalation = escalations.find(e => !e.acknowledged);
  const color = activeEscalation ? getLevelColor(activeEscalation.level) : "red";

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="text-center space-y-4">
        <div className={clsx(
          "w-16 h-16 rounded-full flex items-center justify-center mx-auto",
          color === "red" ? "bg-red-50" :
            color === "amber" ? "bg-amber-50" :
              "bg-blue-50"
        )}>
          <AlertTriangle className={clsx(
            "w-8 h-8",
            color === "red" ? "text-red-600" :
              color === "amber" ? "text-amber-600" :
                "text-blue-600"
          )} />
        </div>
        <h1 className="text-3xl font-bold text-gray-900">
          {activeEscalation?.level === 3 ? "Critical Alert" :
            activeEscalation?.level === 2 ? "Drift Threshold Exceeded" :
              "Health Advisory"}
        </h1>
        <p className="text-gray-600 max-w-lg mx-auto">
          Pulse AI has detected a sustained deviation in your physiological baseline.
          While this is not a diagnosis, professional consultation is recommended.
        </p>
      </div>

      {/* Active Alert Card */}
      {activeEscalation && (
        <Card className={clsx(
          "border",
          color === "red" ? "border-red-200 bg-red-50/30" :
            color === "amber" ? "border-amber-200 bg-amber-50/30" :
              "border-blue-200 bg-blue-50/30"
        )}>
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className={clsx(
                "font-semibold",
                color === "red" ? "text-red-900" :
                  color === "amber" ? "text-amber-900" :
                    "text-blue-900"
              )}>
                Level {activeEscalation.level} Alert
              </h3>
              <span className="text-xs text-gray-500">{formatDate(activeEscalation.timestamp)}</span>
            </div>

            <p className={clsx(
              "text-sm mb-4",
              color === "red" ? "text-red-800" :
                color === "amber" ? "text-amber-800" :
                  "text-blue-800"
            )}>
              {activeEscalation.message}
            </p>

            <h4 className={clsx(
              "font-semibold mb-2 text-sm",
              color === "red" ? "text-red-900" :
                color === "amber" ? "text-amber-900" :
                  "text-blue-900"
            )}>
              Why are you seeing this?
            </h4>
            <ul className={clsx(
              "list-disc list-inside text-sm space-y-1",
              color === "red" ? "text-red-800" :
                color === "amber" ? "text-amber-800" :
                  "text-blue-800"
            )}>
              <li>CareScore exceeded threshold for consecutive days.</li>
              <li>Resting Heart Rate deviation above baseline.</li>
              <li>Cross-signal validation confirmed pattern.</li>
            </ul>
          </div>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Button variant="outline" className="h-auto py-6 flex flex-col items-center gap-2 hover:border-gray-400">
          <Calendar className="w-6 h-6 text-gray-900" />
          <span className="font-semibold">Schedule Consultation</span>
          <span className="text-xs text-gray-500 font-normal">Book with your physician</span>
        </Button>

        <Button variant="outline" className="h-auto py-6 flex flex-col items-center gap-2 hover:border-gray-400">
          <Phone className="w-6 h-6 text-gray-900" />
          <span className="font-semibold">Request Callback</span>
          <span className="text-xs text-gray-500 font-normal">Available in ~15 mins</span>
        </Button>
      </div>

      {/* Dismiss Button */}
      {activeEscalation && (
        <div className="text-center">
          <Button
            variant="secondary"
            className="text-gray-500"
            onClick={() => handleAcknowledge(activeEscalation.id, 'dismissed')}
            disabled={dismissing === activeEscalation.id}
          >
            {dismissing === activeEscalation.id
              ? "Processing..."
              : "Dismiss and continue monitoring"}
          </Button>
        </div>
      )}

      {/* Other Active Escalations */}
      {escalations.filter(e => !e.acknowledged && e.id !== activeEscalation?.id).length > 0 && (
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">Other Active Alerts</h3>
          <div className="space-y-3">
            {escalations.filter(e => !e.acknowledged && e.id !== activeEscalation?.id).map((esc) => {
              const c = getLevelColor(esc.level);
              return (
                <div
                  key={esc.id}
                  className={clsx(
                    "flex items-center justify-between p-3 rounded-lg border",
                    c === "red" ? "bg-red-50 border-red-200" :
                      c === "amber" ? "bg-amber-50 border-amber-200" :
                        "bg-blue-50 border-blue-200"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <AlertTriangle className={clsx(
                      "w-4 h-4",
                      c === "red" ? "text-red-500" :
                        c === "amber" ? "text-amber-500" :
                          "text-blue-500"
                    )} />
                    <div>
                      <p className="text-sm font-medium text-gray-900">Level {esc.level} Alert</p>
                      <p className="text-xs text-gray-500">{formatDate(esc.timestamp)}</p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    className="text-xs h-8"
                    onClick={() => handleAcknowledge(esc.id, 'dismissed')}
                    disabled={dismissing === esc.id}
                  >
                    {dismissing === esc.id ? "..." : "Dismiss"}
                  </Button>
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
};
