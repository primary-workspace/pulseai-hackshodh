import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
    Users,
    Activity,
    AlertTriangle,
    TrendingUp,
    TrendingDown,
    Minus,
    RefreshCw,
    Bell,
    Search,
    ChevronRight,
    Clock,
    Heart
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface PatientSummary {
    patient_id: number;
    patient_name: string;
    latest_care_score: number | null;
    care_score_status: string | null;
    connection_status: string;
    last_data_sync: string | null;
}

interface HighRiskPatient {
    patient_id: number;
    patient_name: string;
    care_score: number;
    status: string;
    timestamp: string;
}

interface NotificationStat {
    total: number;
    unread: number;
    high_priority: number;
}

const getRiskColor = (score: number | null) => {
    if (!score) return "text-slate-400";
    if (score >= 70) return "text-red-400";
    if (score >= 50) return "text-amber-400";
    if (score >= 25) return "text-yellow-400";
    return "text-emerald-400";
};

const getRiskBg = (score: number | null) => {
    if (!score) return "bg-slate-700";
    if (score >= 70) return "bg-red-500/20";
    if (score >= 50) return "bg-amber-500/20";
    if (score >= 25) return "bg-yellow-500/20";
    return "bg-emerald-500/20";
};

const getTrendIcon = (status: string | null) => {
    if (status === "worsening") return <TrendingUp className="text-red-400" size={18} />;
    if (status === "improving") return <TrendingDown className="text-emerald-400" size={18} />;
    return <Minus className="text-slate-400" size={18} />;
};

export const DoctorDashboard = () => {
    const navigate = useNavigate();
    const [patients, setPatients] = useState<PatientSummary[]>([]);
    const [highRisk, setHighRisk] = useState<HighRiskPatient[]>([]);
    const [notifications, setNotifications] = useState<NotificationStat>({ total: 0, unread: 0, high_priority: 0 });
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");

    const userId = localStorage.getItem("userId");
    const userName = localStorage.getItem("userName") || "Doctor";

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        if (!userId) return;

        setLoading(true);
        try {
            // Fetch patients
            const patientsRes = await fetch(`${API_BASE}/doctors/dashboard/patients/${userId}`);
            if (patientsRes.ok) {
                const data = await patientsRes.json();
                setPatients(data);
            }

            // Fetch high risk
            const highRiskRes = await fetch(`${API_BASE}/doctors/dashboard/high-risk/${userId}?threshold=50`);
            if (highRiskRes.ok) {
                const data = await highRiskRes.json();
                setHighRisk(data);
            }

            // Fetch notifications
            const notifRes = await fetch(`${API_BASE}/notifications/${userId}/stats`);
            if (notifRes.ok) {
                const data = await notifRes.json();
                setNotifications(data);
            }
        } catch (error) {
            console.error("Error fetching dashboard data:", error);
        } finally {
            setLoading(false);
        }
    };

    const filteredPatients = patients.filter(p =>
        p.patient_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const formatTimeAgo = (dateStr: string | null) => {
        if (!dateStr) return "Never";
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const hours = Math.floor(diff / (1000 * 60 * 60));
        if (hours < 1) return "Just now";
        if (hours < 24) return `${hours}h ago`;
        return `${Math.floor(hours / 24)}d ago`;
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
            {/* Header */}
            <header className="bg-slate-800/50 backdrop-blur border-b border-slate-700 px-6 py-4">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Activity className="w-8 h-8 text-emerald-500" />
                        <div>
                            <h1 className="text-xl font-bold text-white">Doctor Dashboard</h1>
                            <p className="text-sm text-slate-400">Welcome, Dr. {userName}</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* Notifications */}
                        <button className="relative p-2 text-slate-400 hover:text-white transition-colors">
                            <Bell size={24} />
                            {notifications.unread > 0 && (
                                <span className="absolute top-0 right-0 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                                    {notifications.unread}
                                </span>
                            )}
                        </button>

                        {/* Refresh */}
                        <button
                            onClick={fetchDashboardData}
                            className="p-2 text-slate-400 hover:text-white transition-colors"
                        >
                            <RefreshCw size={24} className={loading ? "animate-spin" : ""} />
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-8">
                {/* Stats Cards */}
                <div className="grid md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-slate-400 text-sm">Total Patients</span>
                            <Users className="text-emerald-400" size={20} />
                        </div>
                        <div className="text-3xl font-bold text-white">{patients.length}</div>
                    </div>

                    <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-slate-400 text-sm">High Risk</span>
                            <AlertTriangle className="text-red-400" size={20} />
                        </div>
                        <div className="text-3xl font-bold text-red-400">{highRisk.length}</div>
                    </div>

                    <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-slate-400 text-sm">Pending Requests</span>
                            <Clock className="text-amber-400" size={20} />
                        </div>
                        <div className="text-3xl font-bold text-amber-400">0</div>
                    </div>

                    <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-slate-400 text-sm">Alerts Today</span>
                            <Bell className="text-blue-400" size={20} />
                        </div>
                        <div className="text-3xl font-bold text-blue-400">{notifications.high_priority}</div>
                    </div>
                </div>

                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Patient List */}
                    <div className="lg:col-span-2">
                        <div className="bg-slate-800/50 backdrop-blur rounded-xl border border-slate-700">
                            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-white">Your Patients</h2>
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                    <input
                                        type="text"
                                        placeholder="Search patients..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                                    />
                                </div>
                            </div>

                            <div className="divide-y divide-slate-700">
                                {loading ? (
                                    <div className="p-8 text-center text-slate-400">
                                        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                                        Loading patients...
                                    </div>
                                ) : filteredPatients.length === 0 ? (
                                    <div className="p-8 text-center text-slate-400">
                                        <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
                                        <p>No patients connected yet</p>
                                        <p className="text-sm mt-1">Patients will appear here when they connect with you</p>
                                    </div>
                                ) : (
                                    filteredPatients.map((patient) => (
                                        <div
                                            key={patient.patient_id}
                                            onClick={() => navigate(`/doctor/patient/${patient.patient_id}`)}
                                            className="p-4 hover:bg-slate-700/30 cursor-pointer transition-colors flex items-center justify-between"
                                        >
                                            <div className="flex items-center gap-4">
                                                {/* Avatar */}
                                                <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold">
                                                    {patient.patient_name.charAt(0)}
                                                </div>

                                                <div>
                                                    <h3 className="font-medium text-white">{patient.patient_name}</h3>
                                                    <div className="flex items-center gap-2 text-sm text-slate-400">
                                                        <Clock size={14} />
                                                        Last sync: {formatTimeAgo(patient.last_data_sync)}
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-4">
                                                {/* Care Score */}
                                                <div className={`px-3 py-1 rounded-full ${getRiskBg(patient.latest_care_score)}`}>
                                                    <span className={`font-bold ${getRiskColor(patient.latest_care_score)}`}>
                                                        {patient.latest_care_score ?? "--"}
                                                    </span>
                                                </div>

                                                {/* Trend */}
                                                {getTrendIcon(patient.care_score_status)}

                                                <ChevronRight className="text-slate-400" size={20} />
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>

                    {/* High Risk Alerts */}
                    <div>
                        <div className="bg-slate-800/50 backdrop-blur rounded-xl border border-slate-700">
                            <div className="p-4 border-b border-slate-700">
                                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                    <AlertTriangle className="text-red-400" size={20} />
                                    High Risk Patients
                                </h2>
                            </div>

                            <div className="p-4 space-y-3">
                                {highRisk.length === 0 ? (
                                    <div className="text-center py-6 text-slate-400">
                                        <Heart className="w-10 h-10 mx-auto mb-2 text-emerald-400" />
                                        <p className="text-sm">All patients stable</p>
                                    </div>
                                ) : (
                                    highRisk.map((patient) => (
                                        <div
                                            key={patient.patient_id}
                                            onClick={() => navigate(`/doctor/patient/${patient.patient_id}`)}
                                            className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl cursor-pointer hover:bg-red-500/20 transition-colors"
                                        >
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="font-medium text-white">{patient.patient_name}</span>
                                                <span className="text-red-400 font-bold">{patient.care_score}</span>
                                            </div>
                                            <p className="text-sm text-red-300">{patient.status}</p>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* Quick Actions */}
                        <div className="mt-6 bg-slate-800/50 backdrop-blur rounded-xl border border-slate-700 p-4">
                            <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
                            <div className="space-y-2">
                                <button
                                    onClick={() => navigate("/doctor/pending-requests")}
                                    className="w-full p-3 bg-slate-700/50 hover:bg-slate-700 rounded-lg text-left text-slate-300 transition-colors flex items-center justify-between"
                                >
                                    View Pending Requests
                                    <ChevronRight size={18} />
                                </button>
                                <button
                                    onClick={() => navigate("/notifications")}
                                    className="w-full p-3 bg-slate-700/50 hover:bg-slate-700 rounded-lg text-left text-slate-300 transition-colors flex items-center justify-between"
                                >
                                    View All Notifications
                                    <ChevronRight size={18} />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default DoctorDashboard;
