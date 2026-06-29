import { Routes, Route, useLocation, Navigate } from "react-router-dom";
import { AuthProvider } from "./Auth/auth.context";
import Footer from "./pages/Home/Footer";
import Home from "./pages/Home/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Profile from "./pages/Profile";
import DashboardPage from "./pages/DashboardPage";
import ProblemsPage from "./pages/ProblemsPage";
import ProgressPage from "./pages/ProgressPage";
import RecommendedPage from "./pages/RecommendedPage";
import ProblemCompilerPage from "./pages/ProblemCompilerPage";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import ToastProvider from './components/ToastProvider';
import ScrollToTop from "./components/ScrollToTop";

// ── User app shell ──
import ProtectedUserRoute from "./Auth/ProtectedUserRoute";
import UserAppLayout from "./components/UserAppLayout";

// ── Admin imports ──
import ProtectedAdminRoute from "./Auth/ProtectedAdminRoute";
import AdminLayout from "./admin/AdminLayout";
import AdminOverview from "./admin/pages/AdminOverview";
import AdminUsers from "./admin/pages/AdminUsers";
import AdminProblems from "./admin/pages/AdminProblems";
import AdminSubmissions from "./admin/pages/AdminSubmissions";
import AdminAnalytics from "./admin/pages/AdminAnalytics";
import AdminTags from "./admin/pages/AdminTags";
import AdminAiFeedback from "./admin/pages/AdminAiFeedback";
import AdminNotifications from "./admin/pages/AdminNotifications";
import AdminSettings from "./admin/pages/AdminSettings";

function App() {
    const location = useLocation();
    const isAdminRoute = location.pathname.startsWith("/admin");

    return (
        <AuthProvider>
            <ToastProvider>
                <ScrollToTop />
                <div style={{ display: "flex", overflow: "hidden", minHeight: "100vh" }}>
                    <div style={{ flex: 1, minWidth: 0, overflow: "auto", display: "flex", flexDirection: "column" }}>
                        <Routes>
                            <Route path="/" element={<Home />} />
                            <Route path="/login" element={<Login />} />
                            <Route path="/register" element={<Register />} />
                            <Route path="/forgot-password" element={<ForgotPassword />} />
                            <Route path="/reset-password" element={<ResetPassword />} />

                            <Route element={<ProtectedUserRoute />}>
                                <Route element={<UserAppLayout />}>
                                    <Route path="/dashboard" element={<DashboardPage />} />
                                    <Route path="/problems" element={<ProblemsPage />} />
                                    <Route path="/problems/:id" element={<ProblemCompilerPage />} />
                                    <Route path="/recommended" element={<RecommendedPage />} />
                                    <Route path="/progress" element={<ProgressPage />} />
                                    <Route path="/profile" element={<Profile />} />
                                </Route>
                            </Route>

                            <Route element={<ProtectedAdminRoute />}>
                                <Route path="/admin" element={<AdminLayout />}>
                                    <Route index element={<Navigate to="overview" replace />} />
                                    <Route path="overview" element={<AdminOverview />} />
                                    <Route path="users" element={<AdminUsers />} />
                                    <Route path="problems" element={<AdminProblems />} />
                                    <Route path="submissions" element={<AdminSubmissions />} />
                                    <Route path="analytics" element={<AdminAnalytics />} />
                                    <Route path="tags" element={<AdminTags />} />
                                    <Route path="ai-feedback" element={<AdminAiFeedback />} />
                                    <Route path="notifications" element={<AdminNotifications />} />
                                    <Route path="settings" element={<AdminSettings />} />
                                </Route>
                            </Route>
                        </Routes>
                    </div>
                </div>
            </ToastProvider>
            {!isAdminRoute && <Footer />}
        </AuthProvider>
    );
}

export default App;
