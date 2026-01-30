import { Card } from "../components/ui/Card";

export const About = () => {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">About Pulse AI</h1>
        <p className="text-gray-500 mt-1">System Architecture & Methodology.</p>
      </div>

      <div className="prose prose-gray max-w-none">
        <p className="text-lg text-gray-600 leading-relaxed">
            Pulse AI is a continuous clinical surveillance platform designed to detect sustained health anomalies 
            before they become critical. Unlike traditional diagnostic tools, Pulse AI focuses on 
            <strong> change detection</strong> relative to a user's personalized baseline.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 my-8">
            <Card className="bg-gray-50 border-0">
                <h3 className="font-bold text-gray-900 mb-2">Data Privacy</h3>
                <p className="text-sm text-gray-600">
                    All processing happens locally or in HIPAA-compliant enclaves. 
                    We never sell health data.
                </p>
            </Card>
            <Card className="bg-gray-50 border-0">
                <h3 className="font-bold text-gray-900 mb-2">Clinical Validation</h3>
                <p className="text-sm text-gray-600">
                    Our algorithms are validated against standard clinical drift models 
                    used in ICU settings.
                </p>
            </Card>
        </div>

        <h3 className="text-xl font-bold text-gray-900 mt-8 mb-4">How CareScore is Calculated</h3>
        <ul className="space-y-4 text-gray-600">
            <li className="flex gap-3">
                <span className="font-mono font-bold text-gray-900">01</span>
                <span><strong>Severity Score (40%):</strong> Magnitude of deviation from personal baseline (Z-score).</span>
            </li>
            <li className="flex gap-3">
                <span className="font-mono font-bold text-gray-900">02</span>
                <span><strong>Persistence Score (25%):</strong> Duration of the detected deviation.</span>
            </li>
            <li className="flex gap-3">
                <span className="font-mono font-bold text-gray-900">03</span>
                <span><strong>Cross-Signal Validation (20%):</strong> Agreement across multiple independent bio-signals.</span>
            </li>
            <li className="flex gap-3">
                <span className="font-mono font-bold text-gray-900">04</span>
                <span><strong>Manual Risk Modifier (15%):</strong> Patient-reported outcomes and spot checks.</span>
            </li>
        </ul>
      </div>
    </div>
  );
};
