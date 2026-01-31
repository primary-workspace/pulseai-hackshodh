import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
    User,
    Stethoscope,
    Heart,
    ArrowRight,
    Activity
} from "lucide-react";

interface RoleCardProps {
    role: "patient" | "doctor" | "caretaker";
    title: string;
    description: string;
    icon: React.ReactNode;
    features: string[];
    selected: boolean;
    onSelect: () => void;
}

const RoleCard = ({ title, description, icon, features, selected, onSelect }: RoleCardProps) => (
    <div
        onClick={onSelect}
        className={`
      relative p-6 rounded-2xl cursor-pointer transition-all duration-300 border-2
      ${selected
                ? "border-emerald-500 bg-emerald-500/10 shadow-lg shadow-emerald-500/20"
                : "border-slate-700 bg-slate-800/50 hover:border-slate-600 hover:bg-slate-800"
            }
    `}
    >
        {/* Selection indicator */}
        {selected && (
            <div className="absolute top-4 right-4 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
            </div>
        )}

        {/* Icon */}
        <div className={`
      w-16 h-16 rounded-xl flex items-center justify-center mb-4
      ${selected ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-700 text-slate-300"}
    `}>
            {icon}
        </div>

        {/* Content */}
        <h3 className={`text-xl font-bold mb-2 ${selected ? "text-emerald-400" : "text-white"}`}>
            {title}
        </h3>
        <p className="text-slate-400 text-sm mb-4">{description}</p>

        {/* Features */}
        <ul className="space-y-2">
            {features.map((feature, index) => (
                <li key={index} className="flex items-center gap-2 text-sm text-slate-300">
                    <div className={`w-1.5 h-1.5 rounded-full ${selected ? "bg-emerald-400" : "bg-slate-500"}`} />
                    {feature}
                </li>
            ))}
        </ul>
    </div>
);

export const RoleSelection = () => {
    const [selectedRole, setSelectedRole] = useState<"patient" | "doctor" | "caretaker" | null>(null);
    const navigate = useNavigate();

    const roles = [
        {
            role: "patient" as const,
            title: "Patient",
            description: "Track your health metrics and get personalized insights",
            icon: <User size={32} />,
            features: [
                "Personal health dashboard",
                "CareScore monitoring",
                "Connect with doctors",
                "Wearable data sync"
            ]
        },
        {
            role: "doctor" as const,
            title: "Healthcare Provider",
            description: "Monitor patients and provide clinical guidance",
            icon: <Stethoscope size={32} />,
            features: [
                "Patient monitoring dashboard",
                "Clinical triage tools",
                "Health trend analysis",
                "Alert notifications"
            ]
        },
        {
            role: "caretaker" as const,
            title: "Caretaker / Family",
            description: "Keep an eye on your loved ones' health status",
            icon: <Heart size={32} />,
            features: [
                "Simplified status view",
                "Real-time health alerts",
                "Emergency notifications",
                "Peace of mind"
            ]
        }
    ];

    const handleContinue = () => {
        if (selectedRole === "patient") {
            navigate("/signup/patient");
        } else if (selectedRole === "doctor") {
            navigate("/signup/doctor");
        } else if (selectedRole === "caretaker") {
            navigate("/signup/caretaker");
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
            {/* Header */}
            <header className="p-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Activity className="w-8 h-8 text-emerald-500" />
                    <span className="text-xl font-bold text-white">Pulse AI</span>
                </div>
                <a
                    href="/login"
                    className="text-slate-400 hover:text-white transition-colors"
                >
                    Already have an account? <span className="text-emerald-400">Sign in</span>
                </a>
            </header>

            {/* Main Content */}
            <main className="flex-1 flex flex-col items-center justify-center px-6 py-12">
                <div className="max-w-4xl w-full">
                    {/* Title */}
                    <div className="text-center mb-12">
                        <h1 className="text-4xl font-bold text-white mb-4">
                            Welcome to <span className="text-emerald-400">Pulse AI</span>
                        </h1>
                        <p className="text-xl text-slate-400">
                            Select how you'll be using the platform
                        </p>
                    </div>

                    {/* Role Cards */}
                    <div className="grid md:grid-cols-3 gap-6 mb-12">
                        {roles.map((role) => (
                            <RoleCard
                                key={role.role}
                                {...role}
                                selected={selectedRole === role.role}
                                onSelect={() => setSelectedRole(role.role)}
                            />
                        ))}
                    </div>

                    {/* Continue Button */}
                    <div className="flex justify-center">
                        <button
                            onClick={handleContinue}
                            disabled={!selectedRole}
                            className={`
                flex items-center gap-3 px-8 py-4 rounded-xl font-semibold text-lg transition-all
                ${selectedRole
                                    ? "bg-emerald-500 text-white hover:bg-emerald-600 shadow-lg shadow-emerald-500/30"
                                    : "bg-slate-700 text-slate-400 cursor-not-allowed"
                                }
              `}
                        >
                            Continue
                            <ArrowRight size={20} />
                        </button>
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="p-6 text-center text-slate-500 text-sm">
                By continuing, you agree to our Terms of Service and Privacy Policy
            </footer>
        </div>
    );
};

export default RoleSelection;
