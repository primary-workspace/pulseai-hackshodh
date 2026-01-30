import { useState } from "react";
import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Save, CheckCircle2, AlertCircle, Activity, Droplet, Heart } from "lucide-react";
import { healthService, authService } from "../lib/api";
import { clsx } from "clsx";

const SYMPTOM_OPTIONS = [
    "Fatigue",
    "Dizziness",
    "Nausea",
    "Headache",
    "Shortness of Breath",
    "Chest Pain",
    "Palpitations",
    "Insomnia"
];

export const ManualEntry = () => {
    const [bpSystolic, setBpSystolic] = useState("");
    const [bpDiastolic, setBpDiastolic] = useState("");
    const [bloodSugar, setBloodSugar] = useState("");
    const [symptoms, setSymptoms] = useState<string[]>([]);

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const userId = authService.getUserId();

    const toggleSymptom = (symptom: string) => {
        setSymptoms(prev =>
            prev.includes(symptom)
                ? prev.filter(s => s !== symptom)
                : [...prev, symptom]
        );
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setError(null);
        setSuccess(false);

        try {
            if (!userId) {
                throw new Error("Please log in to submit health data");
            }

            const data: {
                bp_systolic?: number;
                bp_diastolic?: number;
                blood_sugar?: number;
                symptoms?: string[];
            } = {};

            if (bpSystolic) data.bp_systolic = parseInt(bpSystolic, 10);
            if (bpDiastolic) data.bp_diastolic = parseInt(bpDiastolic, 10);
            if (bloodSugar) data.blood_sugar = parseInt(bloodSugar, 10);
            if (symptoms.length > 0) data.symptoms = symptoms;

            // Check if any data was entered
            if (Object.keys(data).length === 0) {
                throw new Error("Please enter at least one measurement or symptom");
            }

            await healthService.submitManualEntry(data);

            setSuccess(true);

            // Reset form after success
            setTimeout(() => {
                setBpSystolic("");
                setBpDiastolic("");
                setBloodSugar("");
                setSymptoms([]);
                setSuccess(false);
            }, 3000);

        } catch (err: any) {
            console.error('Manual entry error:', err);
            setError(err.message || err.response?.data?.detail || "Failed to save entry");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Manual Entry</h1>
                <p className="text-gray-500 mt-1">Log spot checks and symptoms to improve accuracy.</p>
            </div>

            {success && (
                <div className="flex items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    <p className="text-emerald-800 font-medium">Data logged successfully! Analysis will update shortly.</p>
                </div>
            )}

            {error && (
                <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <AlertCircle className="w-5 h-5 text-red-600" />
                    <p className="text-red-800">{error}</p>
                    <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">×</button>
                </div>
            )}

            <Card>
                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Blood Pressure Section */}
                    <div>
                        <div className="flex items-center gap-2 mb-4">
                            <Heart className="w-5 h-5 text-red-500" />
                            <label className="text-sm font-semibold text-gray-900">Blood Pressure</label>
                        </div>
                        <div className="grid grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-sm text-gray-600">Systolic (mmHg)</label>
                                <input
                                    type="number"
                                    value={bpSystolic}
                                    onChange={(e) => setBpSystolic(e.target.value)}
                                    min="60"
                                    max="250"
                                    className="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-900 outline-none transition-all"
                                    placeholder="120"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-gray-600">Diastolic (mmHg)</label>
                                <input
                                    type="number"
                                    value={bpDiastolic}
                                    onChange={(e) => setBpDiastolic(e.target.value)}
                                    min="40"
                                    max="150"
                                    className="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-900 outline-none transition-all"
                                    placeholder="80"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Blood Glucose Section */}
                    <div>
                        <div className="flex items-center gap-2 mb-4">
                            <Droplet className="w-5 h-5 text-blue-500" />
                            <label className="text-sm font-semibold text-gray-900">Blood Glucose</label>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-gray-600">Level (mg/dL)</label>
                            <input
                                type="number"
                                value={bloodSugar}
                                onChange={(e) => setBloodSugar(e.target.value)}
                                min="20"
                                max="600"
                                className="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-900 outline-none transition-all"
                                placeholder="90"
                            />
                        </div>
                    </div>

                    {/* Symptoms Section */}
                    <div>
                        <div className="flex items-center gap-2 mb-4">
                            <Activity className="w-5 h-5 text-amber-500" />
                            <label className="text-sm font-semibold text-gray-900">Symptoms</label>
                            {symptoms.length > 0 && (
                                <span className="text-xs text-gray-500 ml-2">({symptoms.length} selected)</span>
                            )}
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            {SYMPTOM_OPTIONS.map((symptom) => {
                                const isSelected = symptoms.includes(symptom);
                                return (
                                    <label
                                        key={symptom}
                                        className={clsx(
                                            "flex items-center gap-2 p-3 border rounded-lg cursor-pointer transition-all",
                                            isSelected
                                                ? "border-gray-900 bg-gray-50"
                                                : "border-gray-100 hover:bg-gray-50"
                                        )}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={isSelected}
                                            onChange={() => toggleSymptom(symptom)}
                                            className="rounded text-gray-900 focus:ring-gray-900"
                                        />
                                        <span className={clsx(
                                            "text-sm",
                                            isSelected ? "text-gray-900 font-medium" : "text-gray-700"
                                        )}>
                                            {symptom}
                                        </span>
                                    </label>
                                );
                            })}
                        </div>
                    </div>

                    {/* Submit Button */}
                    <div className="pt-4">
                        <Button
                            type="submit"
                            className="w-full gap-2 h-12"
                            disabled={isSubmitting || success}
                        >
                            {isSubmitting ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    Saving...
                                </>
                            ) : success ? (
                                <>
                                    <CheckCircle2 className="w-4 h-4" /> Data Logged Successfully
                                </>
                            ) : (
                                <>
                                    <Save className="w-4 h-4" /> Save Entry
                                </>
                            )}
                        </Button>
                    </div>
                </form>
            </Card>

            {/* Info Card */}
            <Card className="bg-blue-50 border-blue-200">
                <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-800">
                        <p className="font-semibold mb-1">Why Manual Entry Matters</p>
                        <p>
                            Manual readings and symptom reports are weighted in CareScore calculations.
                            They help validate wearable data and improve drift detection accuracy.
                        </p>
                    </div>
                </div>
            </Card>
        </div>
    );
};
