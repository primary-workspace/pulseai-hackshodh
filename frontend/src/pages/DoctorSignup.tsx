import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
    Stethoscope,
    Building2,
    FileCheck,
    ArrowLeft,
    Activity,
    Loader2
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface DoctorFormData {
    email: string;
    name: string;
    phone: string;
    full_name: string;
    specialization: string;
    qualification: string;
    hospital_name: string;
    hospital_address: string;
    city: string;
    state: string;
    country: string;
    emergency_contact: string;
    license_number: string;
}

const specializations = [
    "General Medicine",
    "Cardiology",
    "Pulmonology",
    "Endocrinology",
    "Neurology",
    "Gastroenterology",
    "Nephrology",
    "Oncology",
    "Orthopedics",
    "Dermatology",
    "Psychiatry",
    "Pediatrics",
    "Geriatrics",
    "Emergency Medicine",
    "Family Medicine",
    "Internal Medicine"
];

export const DoctorSignup = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const [formData, setFormData] = useState<DoctorFormData>({
        email: "",
        name: "",
        phone: "",
        full_name: "",
        specialization: "",
        qualification: "",
        hospital_name: "",
        hospital_address: "",
        city: "",
        state: "",
        country: "India",
        emergency_contact: "",
        license_number: ""
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));

        // Sync name fields
        if (name === "name") {
            setFormData(prev => ({ ...prev, full_name: value }));
        }
    };

    const isStep1Valid = formData.email && formData.name && formData.phone;
    const isStep2Valid = formData.specialization && formData.qualification;
    const isStep3Valid = formData.hospital_name && formData.city;

    const handleSubmit = async () => {
        setLoading(true);
        setError("");

        try {
            const response = await fetch(`${API_BASE}/auth/register/doctor`, {
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
            localStorage.setItem("userRole", "doctor");
            localStorage.setItem("userName", data.user.name);

            navigate("/doctor-dashboard");
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

            <main className="max-w-2xl mx-auto px-6 py-12">
                {/* Progress Steps */}
                <div className="flex items-center justify-between mb-12">
                    {[1, 2, 3].map((s) => (
                        <div key={s} className="flex items-center">
                            <div className={`
                w-10 h-10 rounded-full flex items-center justify-center font-bold
                ${step >= s ? "bg-emerald-500 text-white" : "bg-slate-700 text-slate-400"}
              `}>
                                {s}
                            </div>
                            {s < 3 && (
                                <div className={`w-24 h-1 mx-2 ${step > s ? "bg-emerald-500" : "bg-slate-700"}`} />
                            )}
                        </div>
                    ))}
                </div>

                {/* Form Card */}
                <div className="bg-slate-800/50 backdrop-blur rounded-2xl p-8 border border-slate-700">
                    {/* Step 1: Basic Info */}
                    {step === 1 && (
                        <>
                            <div className="flex items-center gap-3 mb-6">
                                <Stethoscope className="w-8 h-8 text-emerald-400" />
                                <h2 className="text-2xl font-bold text-white">Personal Information</h2>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-slate-300 mb-2">Full Name *</label>
                                    <input
                                        type="text"
                                        name="name"
                                        value={formData.name}
                                        onChange={handleChange}
                                        className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                        placeholder="Dr. John Smith"
                                    />
                                </div>

                                <div>
                                    <label className="block text-slate-300 mb-2">Email Address *</label>
                                    <input
                                        type="email"
                                        name="email"
                                        value={formData.email}
                                        onChange={handleChange}
                                        className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                        placeholder="doctor@hospital.com"
                                    />
                                </div>

                                <div>
                                    <label className="block text-slate-300 mb-2">Phone Number *</label>
                                    <input
                                        type="tel"
                                        name="phone"
                                        value={formData.phone}
                                        onChange={handleChange}
                                        className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                        placeholder="+91 98765 43210"
                                    />
                                </div>
                            </div>
                        </>
                    )}

                    {/* Step 2: Professional Info */}
                    {step === 2 && (
                        <>
                            <div className="flex items-center gap-3 mb-6">
                                <FileCheck className="w-8 h-8 text-emerald-400" />
                                <h2 className="text-2xl font-bold text-white">Professional Details</h2>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-slate-300 mb-2">Specialization *</label>
                                    <select
                                        name="specialization"
                                        value={formData.specialization}
                                        onChange={handleChange}
                                        className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                    >
                                        <option value="">Select Specialization</option>
                                        {specializations.map(s => (
                                            <option key={s} value={s}>{s}</option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-slate-300 mb-2">Qualification *</label>
                                    <input
                                        type="text"
                                        name="qualification"
                                        value={formData.qualification}
                                        onChange={handleChange}
                                        className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                        placeholder="MBBS, MD (Cardiology)"
                                    />
                                </div>

                                <div>
                                    <label className="block text-slate-300 mb-2">Medical License Number (optional)</label>
                                    <input
                                        type="text"
                                        name="license_number"
                                        value={formData.license_number}
                                        onChange={handleChange}
                                        className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                        placeholder="MCI/NMC Registration Number"
                                    />
                                </div>
                            </div>
                        </>
                    )}

                    {/* Step 3: Hospital Info */}
                    {step === 3 && (
                        <>
                            <div className="flex items-center gap-3 mb-6">
                                <Building2 className="w-8 h-8 text-emerald-400" />
                                <h2 className="text-2xl font-bold text-white">Hospital / Clinic</h2>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-slate-300 mb-2">Hospital / Clinic Name *</label>
                                    <input
                                        type="text"
                                        name="hospital_name"
                                        value={formData.hospital_name}
                                        onChange={handleChange}
                                        className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                        placeholder="Apollo Hospital"
                                    />
                                </div>

                                <div>
                                    <label className="block text-slate-300 mb-2">Address</label>
                                    <textarea
                                        name="hospital_address"
                                        value={formData.hospital_address}
                                        onChange={handleChange}
                                        rows={2}
                                        className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500 resize-none"
                                        placeholder="123 Medical Street"
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-slate-300 mb-2">City *</label>
                                        <input
                                            type="text"
                                            name="city"
                                            value={formData.city}
                                            onChange={handleChange}
                                            className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                            placeholder="Mumbai"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-slate-300 mb-2">State</label>
                                        <input
                                            type="text"
                                            name="state"
                                            value={formData.state}
                                            onChange={handleChange}
                                            className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                            placeholder="Maharashtra"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-slate-300 mb-2">Emergency Contact</label>
                                    <input
                                        type="tel"
                                        name="emergency_contact"
                                        value={formData.emergency_contact}
                                        onChange={handleChange}
                                        className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-emerald-500"
                                        placeholder="+91 98765 43210"
                                    />
                                </div>
                            </div>
                        </>
                    )}

                    {/* Error Message */}
                    {error && (
                        <div className="mt-4 p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-400">
                            {error}
                        </div>
                    )}

                    {/* Navigation Buttons */}
                    <div className="flex justify-between mt-8">
                        {step > 1 ? (
                            <button
                                onClick={() => setStep(s => s - 1)}
                                className="px-6 py-3 bg-slate-700 text-white rounded-xl hover:bg-slate-600 transition-colors"
                            >
                                Back
                            </button>
                        ) : (
                            <div />
                        )}

                        {step < 3 ? (
                            <button
                                onClick={() => setStep(s => s + 1)}
                                disabled={step === 1 ? !isStep1Valid : !isStep2Valid}
                                className={`
                  px-6 py-3 rounded-xl font-semibold transition-colors
                  ${(step === 1 ? isStep1Valid : isStep2Valid)
                                        ? "bg-emerald-500 text-white hover:bg-emerald-600"
                                        : "bg-slate-700 text-slate-400 cursor-not-allowed"
                                    }
                `}
                            >
                                Continue
                            </button>
                        ) : (
                            <button
                                onClick={handleSubmit}
                                disabled={!isStep3Valid || loading}
                                className={`
                  flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-colors
                  ${isStep3Valid && !loading
                                        ? "bg-emerald-500 text-white hover:bg-emerald-600"
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
                                    "Complete Registration"
                                )}
                            </button>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default DoctorSignup;
