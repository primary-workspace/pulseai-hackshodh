import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
    Heart,
    Activity,
    RefreshCw,
    Bell,
    AlertTriangle,
    CheckCircle,
    Phone,
    Clock
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface PatientStatus {
    patient_id: number;
    patient_name: string;
    risk_level: "stable" | "mild" | "moderate" | "high";
    care_score: number | null;
    last_update: string | null;
    has_recent_anomaly: boolean;
}

const getRiskCard = (risk: string) => {
    switch (risk) {
        case "high":
            return {
                bg: "bg-gradient-to-br from-red-600 to-red-800",
                icon: AlertTriangle,
                label: "Requires Attention",
                borderColor: "border-red-500"
            };
        case "moderate":
            return {
                bg: "bg-gradient-to-br from-amber-600 to-amber-800",
                icon: AlertTriangle,
                label: "Monitoring Recommended",
                borderColor: "border-amber-500"
            };
        case "mild":
            return {
                bg: "bg-gradient-to-br from-yellow-600 to-yellow-800",
                icon: Activity,
                label: "Minor Concerns",
                borderColor: "border-yellow-500"
            };
        default:
            return {
                bg: "bg-gradient-to-br from-emerald-600 to-emerald-800",
                icon: CheckCircle,
                label: "All Normal",
                borderColor: "border-emerald-500"
            };
    }
};

export const CaretakerDashboard = () => {
    const navigate = useNavigate();
    const [patients, setPatients] = useState<PatientStatus[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedPatient, setSelectedPatient] = useState<number | null>(null);
    const [patientDetails, setPatientDetails] = useState<any>(null);

    const userId = localStorage.getItem("userId");
    const userName = localStorage.getItem("userName") || "Caretaker";

    useEffect(() => {
        fetchPatients();
    }, []);

    const fetchPatients = async () => {
        if (!userId) return;

        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/caretakers/dashboard/patients/${userId}`);
            if (res.ok) {
                const data = await res.json();
                setPatients(data);
                if (data.length > 0 && !selectedPatient) {
                    setSelectedPatient(data[0].patient_id);
                }
            }
        } catch (error) {
            console.error("Error fetching patients:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (selectedPatient) {
            fetchPatientDetails(selectedPatient);
        }
    }, [selectedPatient]);

    const fetchPatientDetails = async (patientId: number) => {
        if (!userId) return;

        try {
            const res = await fetch(`${API_BASE}/caretakers/dashboard/patients/${userId}/${patientId}`);
            if (res.ok) {
                const data = await res.json();
                setPatientDetails(data);
            }
        } catch (error) {
            console.error("Error fetching patient details:", error);
        }
    };

    const formatTimeAgo = (dateStr: string | null) => {
        if (!dateStr) return "Never updated";
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const hours = Math.floor(diff / (1000 * 60 * 60));
        if (hours < 1) return "Just now";
        if (hours < 24) return `${hours} hours ago`;
        return `${Math.floor(hours / 24)} days ago`;
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
            {/* Header */}
            <header className="bg-slate-800/50 backdrop-blur border-b border-slate-700 px-6 py-4">
                <div className="max-w-4xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Heart className="w-8 h-8 text-rose-500" />
                        <div>
                            <h1 className="text-xl font-bold text-white">Family Care</h1>
                            <p className="text-sm text-slate-400">Hello, {userName}</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <button className="p-2 text-slate-400 hover:text-white transition-colors">
                            <Bell size={24} />
                        </button>
                        <button
                            onClick={fetchPatients}
                            className="p-2 text-slate-400 hover:text-white transition-colors"
                        >
                            <RefreshCw size={24} className={loading ? "animate-spin" : ""} />
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-6 py-8">
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-20">
                        <RefreshCw className="w-12 h-12 text-emerald-400 animate-spin mb-4" />
                        <p className="text-slate-400">Loading health status...</p>
                    </div>
                ) : patients.length === 0 ? (
                    <div className="text-center py-20">
                        <Heart className="w-16 h-16 mx-auto mb-4 text-slate-600" />
                        <h2 className="text-2xl font-bold text-white mb-2">No patients connected</h2>
                        <p className="text-slate-400 mb-6">
                            Ask your loved one to add you as a caretaker in their Pulse AI settings
                        </p>
                    </div>
                ) : (
                    <>
                        {/* Patient Tabs */}
                        {patients.length > 1 && (
                            <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                                {patients.map((patient) => {
                                    const riskInfo = getRiskCard(patient.risk_level);
                                    return (
                                        <button
                                            key={patient.patient_id}
                                            onClick={() => setSelectedPatient(patient.patient_id)}
                                            className={`
                        px-4 py-2 rounded-xl flex items-center gap-2 whitespace-nowrap transition-all
                        ${selectedPatient === patient.patient_id
                                                    ? `${riskInfo.bg} text-white shadow-lg`
                                                    : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                                                }
                      `}
                                        >
                                            <span className="font-medium">{patient.patient_name}</span>
                                            {patient.has_recent_anomaly && (
                                                <span className="w-2 h-2 bg-red-400 rounded-full animate-pulse" />
                                            )}
                                        </button>
                                    );
                                })}
                            </div>
                        )}

                        {/* Main Status Card */}
                        {patientDetails && (
                            <div className="space-y-6">
                                {/* Big Status Card */}
                                <div className={`
                  rounded-3xl p-8 text-white shadow-2xl
                  ${getRiskCard(patientDetails.risk_level).bg}
                `}>
                                    <div className="flex items-start justify-between mb-6">
                                        <div>
                                            <h2 className="text-3xl font-bold mb-2">{patientDetails.patient_name}</h2>
                                            <p className="text-white/80 flex items-center gap-2">
                                                <Clock size={16} />
                                                Updated {formatTimeAgo(patientDetails.last_update)}
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            {patientDetails.care_score && (
                                                <div className="text-5xl font-bold">{patientDetails.care_score}</div>
                                            )}
                                            <p className="text-white/70 text-sm">CareScore</p>
                                        </div>
                                    </div>

                                    {/* Status Message */}
                                    <div className="bg-black/20 rounded-2xl p-6">
                                        <div className="flex items-center gap-3 mb-3">
                                            {(() => {
                                                const Icon = getRiskCard(patientDetails.risk_level).icon;
                                                return <Icon size={28} />;
                                            })()}
                                            <span className="text-xl font-semibold">
                                                {getRiskCard(patientDetails.risk_level).label}
                                            </span>
                                        </div>
                                        <p className="text-white/90 text-lg">
                                            {patientDetails.status_message}
                                        </p>
                                    </div>
                                </div>

                                {/* What This Means (simple explanation) */}
                                {patientDetails.care_score_explanation && (
                                    <div className="bg-slate-800/50 backdrop-blur rounded-2xl p-6 border border-slate-700">
                                        <h3 className="text-lg font-semibold text-white mb-3">What This Means</h3>
                                        <p className="text-slate-300 leading-relaxed">
                                            {patientDetails.care_score_explanation}
                                        </p>
                                    </div>
                                )}

                                {/* Quick Actions */}
                                <div className="grid grid-cols-2 gap-4">
                                    <a
                                        href={`tel:${patientDetails.emergency_contact || ""}`}
                                        className="flex items-center justify-center gap-3 p-5 bg-emerald-600 hover:bg-emerald-700 rounded-2xl text-white font-semibold transition-colors"
                                    >
                                        <Phone size={24} />
                                        Call Family Member
                                    </a>
                                    <button
                                        onClick={() => navigate("/notifications")}
                                        className="flex items-center justify-center gap-3 p-5 bg-slate-700 hover:bg-slate-600 rounded-2xl text-white font-semibold transition-colors"
                                    >
                                        <Bell size={24} />
                                        Alert History
                                    </button>
                                </div>

                                {/* Disclaimer */}
                                <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
                                    <p className="text-sm text-blue-300">
                                        <strong>Note:</strong> This is a general wellness indicator and not a medical diagnosis.
                                        If you're concerned about your loved one's health, please consult a healthcare professional.
                                    </p>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </main>
        </div>
    );
};

export default CaretakerDashboard;
