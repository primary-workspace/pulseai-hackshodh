import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { DashboardLayout } from "./components/DashboardLayout";
import { LandingPage } from "./pages/LandingPage";
import { Dashboard } from "./pages/Dashboard";
import { Insights } from "./pages/Insights";
import { Escalation } from "./pages/Escalation";
import { ManualEntry } from "./pages/ManualEntry";
import { Settings } from "./pages/Settings";
import { Login } from "./pages/Login";
import { Signup } from "./pages/Signup";
import { DriveSync } from "./pages/DriveSync";
import { RoleSelection } from "./pages/RoleSelection";
import { DoctorSignup } from "./pages/DoctorSignup";
import { CaretakerSignup } from "./pages/CaretakerSignup";
import { DoctorDashboard } from "./pages/DoctorDashboard";
import { CaretakerDashboard } from "./pages/CaretakerDashboard";

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* Role Selection & Role-Specific Signup */}
        <Route path="/get-started" element={<RoleSelection />} />
        <Route path="/role-select" element={<RoleSelection />} />
        <Route path="/signup/patient" element={<Signup />} />
        <Route path="/signup/doctor" element={<DoctorSignup />} />
        <Route path="/signup/caretaker" element={<CaretakerSignup />} />

        {/* Patient Dashboard Routes */}
        <Route
          path="/dashboard"
          element={
            <DashboardLayout>
              <Dashboard />
            </DashboardLayout>
          }
        />
        <Route
          path="/insights"
          element={
            <DashboardLayout>
              <Insights />
            </DashboardLayout>
          }
        />
        <Route
          path="/sync"
          element={
            <DashboardLayout>
              <DriveSync />
            </DashboardLayout>
          }
        />
        <Route
          path="/escalation"
          element={
            <DashboardLayout>
              <Escalation />
            </DashboardLayout>
          }
        />
        <Route
          path="/entry"
          element={
            <DashboardLayout>
              <ManualEntry />
            </DashboardLayout>
          }
        />
        <Route
          path="/settings"
          element={
            <DashboardLayout>
              <Settings />
            </DashboardLayout>
          }
        />

        {/* Doctor Routes */}
        <Route path="/doctor-dashboard" element={<DoctorDashboard />} />

        {/* Caretaker Routes */}
        <Route path="/caretaker-dashboard" element={<CaretakerDashboard />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
