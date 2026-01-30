import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import {
  Save,
  User,
  Bell,
  Shield,
  CheckCircle2,
  Cloud,
  Unlink,
  ExternalLink,
  Loader2,
  Key,
  Trash2
} from "lucide-react";
import { authService, driveService, User as UserType } from "../lib/api";
import { Link } from "react-router-dom";
import { clsx } from "clsx";

export const Settings = () => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // User profile
  const [user, setUser] = useState<UserType | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");

  // Notifications
  const [driftAlerts, setDriftAlerts] = useState(true);
  const [escalationEmails, setEscalationEmails] = useState(true);
  const [weeklyDigest, setWeeklyDigest] = useState(false);

  // OAuth Status
  const [isOAuthConnected, setIsOAuthConnected] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(true);

  const userId = authService.getUserId();

  useEffect(() => {
    loadUserData();
    checkOAuthStatus();
  }, [userId]);

  const loadUserData = () => {
    const storedUser = authService.getCurrentUser();
    if (storedUser) {
      setUser(storedUser);
      setName(storedUser.name || "");
      setEmail(storedUser.email || "");
    }
  };

  const checkOAuthStatus = async () => {
    if (!userId) {
      setOauthLoading(false);
      return;
    }

    try {
      const status = await driveService.checkOAuthStatus(userId);
      setIsOAuthConnected(status.has_valid_oauth);
    } catch (err) {
      console.error('Failed to check OAuth status:', err);
    } finally {
      setOauthLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // Simulate API call (user profile update endpoint would go here)
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Update local storage
    const updatedUser = { ...user, name, email };
    localStorage.setItem('pulse_user', JSON.stringify(updatedUser));
    setUser(updatedUser as UserType);

    setLoading(false);
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  const handleDisconnectDrive = async () => {
    if (!userId) return;

    try {
      setOauthLoading(true);
      await driveService.revokeAccess(userId);
      setIsOAuthConnected(false);
    } catch (err) {
      console.error('Failed to disconnect Drive:', err);
    } finally {
      setOauthLoading(false);
    }
  };

  const handleLogout = () => {
    authService.logout();
    window.location.href = '/login';
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Settings</h1>
        <p className="text-gray-500 mt-1">Manage your account and preferences.</p>
      </div>

      {success && (
        <div className="flex items-center gap-2 p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          <p className="text-emerald-800 font-medium">Settings saved successfully!</p>
        </div>
      )}

      {/* Profile Settings */}
      <Card>
        <CardHeader className="flex items-center gap-2">
          <User className="w-5 h-5 text-gray-400" />
          <CardTitle>Profile Information</CardTitle>
        </CardHeader>
        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-900 outline-none"
                placeholder="John Doe"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-900 outline-none"
                placeholder="john@example.com"
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Phone Number</label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-900 outline-none"
              placeholder="+1 (555) 000-0000"
            />
          </div>
          <Button type="submit" className="gap-2" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" /> Save Changes
              </>
            )}
          </Button>
        </form>
      </Card>

      {/* Data Connections */}
      <Card>
        <CardHeader className="flex items-center gap-2">
          <Cloud className="w-5 h-5 text-gray-400" />
          <CardTitle>Data Connections</CardTitle>
        </CardHeader>
        <div className="space-y-4">
          {/* Google Drive Connection */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className={clsx(
                "w-10 h-10 rounded-full flex items-center justify-center",
                isOAuthConnected ? "bg-emerald-100" : "bg-gray-200"
              )}>
                <Cloud className={clsx(
                  "w-5 h-5",
                  isOAuthConnected ? "text-emerald-600" : "text-gray-400"
                )} />
              </div>
              <div>
                <p className="font-medium text-gray-900">Google Drive</p>
                <p className="text-sm text-gray-500">
                  {oauthLoading ? "Checking..." :
                    isOAuthConnected ? "Connected - Ready to sync" : "Not connected"}
                </p>
              </div>
            </div>
            {oauthLoading ? (
              <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
            ) : isOAuthConnected ? (
              <div className="flex items-center gap-2">
                <Link to="/sync">
                  <Button variant="outline" className="gap-2 text-sm">
                    <ExternalLink className="w-4 h-4" /> Manage
                  </Button>
                </Link>
                <Button
                  variant="outline"
                  className="gap-2 text-sm text-red-600 border-red-200 hover:bg-red-50"
                  onClick={handleDisconnectDrive}
                >
                  <Unlink className="w-4 h-4" /> Disconnect
                </Button>
              </div>
            ) : (
              <Link to="/sync">
                <Button className="gap-2 text-sm">
                  <Cloud className="w-4 h-4" /> Connect
                </Button>
              </Link>
            )}
          </div>
        </div>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-gray-400" />
          <CardTitle>Notification Preferences</CardTitle>
        </CardHeader>
        <div className="space-y-4">
          <label className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors">
            <div>
              <p className="font-medium text-gray-900">Drift Alerts</p>
              <p className="text-sm text-gray-500">Get notified when CareScore changes significantly</p>
            </div>
            <input
              type="checkbox"
              checked={driftAlerts}
              onChange={(e) => setDriftAlerts(e.target.checked)}
              className="w-5 h-5 rounded text-gray-900 focus:ring-gray-900"
            />
          </label>

          <label className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors">
            <div>
              <p className="font-medium text-gray-900">Escalation Emails</p>
              <p className="text-sm text-gray-500">Receive email when escalation is triggered</p>
            </div>
            <input
              type="checkbox"
              checked={escalationEmails}
              onChange={(e) => setEscalationEmails(e.target.checked)}
              className="w-5 h-5 rounded text-gray-900 focus:ring-gray-900"
            />
          </label>

          <label className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors">
            <div>
              <p className="font-medium text-gray-900">Weekly Digest</p>
              <p className="text-sm text-gray-500">Receive a weekly summary of your health trends</p>
            </div>
            <input
              type="checkbox"
              checked={weeklyDigest}
              onChange={(e) => setWeeklyDigest(e.target.checked)}
              className="w-5 h-5 rounded text-gray-900 focus:ring-gray-900"
            />
          </label>
        </div>
      </Card>

      {/* Security Settings */}
      <Card>
        <CardHeader className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-gray-400" />
          <CardTitle>Security</CardTitle>
        </CardHeader>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">API Key</p>
              <p className="text-sm text-gray-500">Your key for webhook authentication</p>
            </div>
            <div className="flex items-center gap-2">
              <code className="text-xs bg-gray-200 px-2 py-1 rounded font-mono">
                ••••••••••••
              </code>
              <Button variant="outline" className="gap-2 text-sm">
                <Key className="w-4 h-4" /> Regenerate
              </Button>
            </div>
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">Two-Factor Authentication</p>
              <p className="text-sm text-gray-500">Add an extra layer of security</p>
            </div>
            <Button variant="outline" className="text-sm">Enable 2FA</Button>
          </div>
        </div>
      </Card>

      {/* Danger Zone */}
      <Card className="border-red-200">
        <CardHeader className="flex items-center gap-2">
          <Trash2 className="w-5 h-5 text-red-400" />
          <CardTitle className="text-red-600">Danger Zone</CardTitle>
        </CardHeader>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">Sign Out</p>
              <p className="text-sm text-gray-500">Sign out of your account on this device</p>
            </div>
            <Button variant="outline" className="text-sm" onClick={handleLogout}>
              Sign Out
            </Button>
          </div>

          <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
            <div>
              <p className="font-medium text-red-700">Delete Account</p>
              <p className="text-sm text-red-600">Permanently delete your account and all data</p>
            </div>
            <Button variant="danger" className="text-sm">Delete Account</Button>
          </div>
        </div>
      </Card>
    </div>
  );
};
