import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
    Heart,
    ArrowLeft,
    Activity,
    Loader2,
    Bell,
    Users
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface CaretakerFormData {
    email: string;
    name: string;
    phone: string;
    full_name: string;
    relationship_type: string;
    notification_preference: string;
}

const relationshipTypes = [
    { value: "family", label: "Family Member" },
    { value: "spouse", label: "Spouse/Partner" },
    { value: "child", label: "Son/Daughter" },
    { value: "parent", label: "Parent" },
    { value: "sibling", label: "Sibling" },
    { value: "professional", label: "Professional Caregiver" },
    { value: "friend", label: "Close Friend" },
    { value: "other", label: "Other" }
];

export const CaretakerSignup = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const [formData, setFormData] = useState<CaretakerFormData>({
        email: "",
        name: "",
        phone: "",
        full_name: "",
        relationship_type: "family",
        notification_preference: "all"
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));

        if (name === "name") {
            setFormData(prev => ({ ...prev, full_name: value }));
        }
    };

    const isFormValid = formData.email && formData.name && formData.phone;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const response = await fetch(`${API_BASE}/auth/register/caretaker`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || "Registration failed");
            }

            const data = await response.json();

            // Store user info
            localStorage.setItem("userId", data.user.id.toString());
            localStorage.setItem("userRole", "caretaker");
            localStorage.setItem("userName", data.user.name);

            navigate("/caretaker-dashboard");
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
            {/* Header */}
            <header className="p-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Activity className="w-8 h-8 text-emerald-500" />
                    <span className="text-xl font-bold text-white">Pulse AI</span>
                </div>
                <button
                    onClick={() => navigate("/role-select")}
                    className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
                >
                    <ArrowLeft size={18} />
                    Back to Role Selection
                </button>
            </header>

            <main className="max-w-lg mx-auto px-6 py-12">
                <div className="bg-slate-800/50 backdrop-blur rounded-2xl p-8 border border-slate-700">
                    {/* Header */}
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-12 h-12 rounded-xl bg-rose-500/20 flex items-center justify-center">
                            <Heart className="w-6 h-6 text-rose-400" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-white">Caretaker Account</h2>
                            <p className="text-slate-400 text-sm">Monitor your loved one's health</p>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* Personal Info */}
                        <div>
                            <label className="block text-slate-300 mb-2">Your Full Name *</label>
                            <input
                                type="text"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                required
                                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                placeholder="John Doe"
                            />
                        </div>

                        <div>
                            <label className="block text-slate-300 mb-2">Email Address *</label>
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                required
                                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                placeholder="john@example.com"
                            />
                        </div>

                        <div>
                            <label className="block text-slate-300 mb-2">Phone Number *</label>
                            <input
                                type="tel"
                                name="phone"
                                value={formData.phone}
                                onChange={handleChange}
                                required
                                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                placeholder="+91 98765 43210"
                            />
                        </div>

                        {/* Relationship */}
                        <div>
                            <label className="block text-slate-300 mb-2">
                                <Users className="inline w-4 h-4 mr-1" />
                                Relationship to Patient
                            </label>
                            <select
                                name="relationship_type"
                                value={formData.relationship_type}
                                onChange={handleChange}
                                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                            >
                                {relationshipTypes.map(type => (
                                    <option key={type.value} value={type.value}>{type.label}</option>
                                ))}
                            </select>
                        </div>

                        {/* Notification Preferences */}
                        <div>
                            <label className="block text-slate-300 mb-2">
                                <Bell className="inline w-4 h-4 mr-1" />
                                Notification Preference
                            </label>
                            <select
                                name="notification_preference"
                                value={formData.notification_preference}
                                onChange={handleChange}
                                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                            >
                                <option value="all">All Updates</option>
                                <option value="critical_only">Critical Alerts Only</option>
                                <option value="daily_summary">Daily Summary</option>
                            </select>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-400">
                                {error}
                            </div>
                        )}

                        {/* Submit */}
                        <button
                            type="submit"
                            disabled={!isFormValid || loading}
                            className={`
                w-full flex items-center justify-center gap-2 py-4 rounded-xl font-semibold transition-colors
                ${isFormValid && !loading
                                    ? "bg-rose-500 text-white hover:bg-rose-600"
                                    : "bg-slate-700 text-slate-400 cursor-not-allowed"
                                }
              `}
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Creating Account...
                                </>
                            ) : (
                                <>
                                    <Heart className="w-5 h-5" />
                                    Create Caretaker Account
                                </>
                            )}
                        </button>
                    </form>

                    {/* Info Note */}
                    <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
                        <p className="text-sm text-blue-300">
                            <strong>What happens next?</strong> After creating your account,
                            you'll receive a connection code to share with your loved one.
                            Once they accept, you'll be able to monitor their health status.
                        </p>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default CaretakerSignup;
