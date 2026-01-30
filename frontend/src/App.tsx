import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
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

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* Protected App Routes */}
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
      </Routes>
    </Router>
  );
}

export default App;
