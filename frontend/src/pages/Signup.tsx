import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { AuthLayout } from "../components/AuthLayout";
import { useState } from "react";
import { ArrowRight, User, Mail, Lock, FileBadge, AlertCircle } from "lucide-react";
import { authService } from "../lib/api";

export const Signup = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [licenseId, setLicenseId] = useState("");
  const [password, setPassword] = useState("");

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const fullName = `${firstName} ${lastName}`.trim();
      await authService.signup(email, fullName, password);
      navigate("/dashboard");
    } catch (err: any) {
      console.error('Signup error:', err);
      if (err.response?.status === 400) {
        setError("An account with this email already exists. Please login instead.");
      } else {
        setError(err.response?.data?.detail || 'Registration failed. Please try again.');
      }
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Request Access"
      subtitle="Join the Pulse AI clinical trial program."
    >
      <form onSubmit={handleSignup} className="space-y-5">
        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-zinc-700">First Name</label>
            <div className="relative group">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400 group-focus-within:text-zinc-900 transition-colors" />
              <input
                type="text"
                required
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 text-zinc-900 focus:ring-2 focus:ring-zinc-900 focus:bg-white outline-none transition-all"
                placeholder="Jane"
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-semibold text-zinc-700">Last Name</label>
            <div className="relative group">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400 group-focus-within:text-zinc-900 transition-colors" />
              <input
                type="text"
                required
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 text-zinc-900 focus:ring-2 focus:ring-zinc-900 focus:bg-white outline-none transition-all"
                placeholder="Doe"
              />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-zinc-700">Work Email</label>
          <div className="relative group">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400 group-focus-within:text-zinc-900 transition-colors" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 text-zinc-900 focus:ring-2 focus:ring-zinc-900 focus:bg-white outline-none transition-all"
              placeholder="name@hospital.com"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-zinc-700">Medical License ID <span className="text-zinc-400 font-normal">(Optional)</span></label>
          <div className="relative group">
            <FileBadge className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400 group-focus-within:text-zinc-900 transition-colors" />
            <input
              type="text"
              value={licenseId}
              onChange={(e) => setLicenseId(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 text-zinc-900 focus:ring-2 focus:ring-zinc-900 focus:bg-white outline-none transition-all"
              placeholder="MD-123456"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-zinc-700">Create Password</label>
          <div className="relative group">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400 group-focus-within:text-zinc-900 transition-colors" />
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 text-zinc-900 focus:ring-2 focus:ring-zinc-900 focus:bg-white outline-none transition-all"
              placeholder="••••••••"
            />
          </div>
        </div>

        <Button
          type="submit"
          className="w-full h-12 text-base font-semibold gap-2 rounded-xl shadow-lg shadow-zinc-900/10 hover:shadow-zinc-900/20 transition-all"
          disabled={loading}
        >
          {loading ? "Processing..." : (
            <>Create Account <ArrowRight className="w-4 h-4" /></>
          )}
        </Button>

        <div className="text-center text-sm text-zinc-500 mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-zinc-900 font-semibold hover:underline">
            Sign in
          </Link>
        </div>
      </form>
    </AuthLayout>
  );
};
