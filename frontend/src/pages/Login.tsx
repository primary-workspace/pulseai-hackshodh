import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { AuthLayout } from "../components/AuthLayout";
import { useState } from "react";
import { ArrowRight, Mail, Lock, AlertCircle } from "lucide-react";
import { authService } from "../lib/api";

export const Login = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await authService.login(email, password);
      navigate("/dashboard");
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
      setLoading(false);
    }
  };

  // Handle demo login
  const handleDemoLogin = async () => {
    setLoading(true);
    setError(null);

    try {
      await authService.login("demo@pulseai.com", "demo123");
      navigate("/dashboard");
    } catch (err: any) {
      // If demo user doesn't exist, create it
      try {
        await authService.signup("demo@pulseai.com", "Demo User", "demo123");
        navigate("/dashboard");
      } catch (signupErr: any) {
        setError("Failed to access demo. Please try again.");
        setLoading(false);
      }
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Enter your credentials to access the clinical console."
    >
      <form onSubmit={handleLogin} className="space-y-5">
        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        <div className="space-y-2">
          <label className="text-sm font-semibold text-zinc-700">Email Address</label>
          <div className="relative group">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400 group-focus-within:text-zinc-900 transition-colors" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 text-zinc-900 placeholder:text-zinc-400 focus:ring-2 focus:ring-zinc-900 focus:bg-white focus:border-transparent outline-none transition-all"
              placeholder="doctor@hospital.com"
            />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <label className="text-sm font-semibold text-zinc-700">Password</label>
            <a href="#" className="text-sm text-blue-600 hover:text-blue-700 font-medium">Forgot password?</a>
          </div>
          <div className="relative group">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400 group-focus-within:text-zinc-900 transition-colors" />
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-zinc-50 border border-zinc-200 text-zinc-900 placeholder:text-zinc-400 focus:ring-2 focus:ring-zinc-900 focus:bg-white focus:border-transparent outline-none transition-all"
              placeholder="••••••••"
            />
          </div>
        </div>

        <Button
          type="submit"
          className="w-full h-12 text-base font-semibold gap-2 rounded-xl shadow-lg shadow-zinc-900/10 hover:shadow-zinc-900/20 transition-all"
          disabled={loading}
        >
          {loading ? "Authenticating..." : (
            <>Sign In <ArrowRight className="w-4 h-4" /></>
          )}
        </Button>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-zinc-200" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white px-2 text-zinc-500">Or</span>
          </div>
        </div>

        <Button
          type="button"
          variant="outline"
          onClick={handleDemoLogin}
          className="w-full h-12 text-base font-medium rounded-xl"
          disabled={loading}
        >
          Try Demo Account
        </Button>

        <div className="text-center text-sm text-zinc-500 mt-6">
          Don't have an account?{" "}
          <Link to="/signup" className="text-zinc-900 font-semibold hover:underline">
            Request access
          </Link>
        </div>
      </form>
    </AuthLayout>
  );
};
