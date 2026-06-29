import React, { useEffect, useState, useCallback } from "react";
import {
  Settings, Cpu, Sparkles, Wrench, Package, Key, Link2, AlertTriangle
} from "lucide-react";
import { updateMaintenanceMode } from "../../api/admin.api";
import { useAdminData } from "../AdminDataContext";
import StatCard from "../components/StatCard";
import ConfirmModal from "../components/ConfirmModal";
import "../../styles/admin.css";

function SettingRow({ icon, label, value, mono = false }) {
  return (
    <div className="admin-setting-row">
      <div className="admin-setting-label">
        {icon}
        <span>{label}</span>
      </div>
      <div className={`admin-setting-value ${mono ? "admin-cell-mono" : ""}`}>
        {value ?? "—"}
      </div>
    </div>
  );
}

export default function AdminSettings() {
  const { getSettings, invalidateSettings, settingsVersion } = useAdminData();

  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [confirmTarget, setConfirmTarget] = useState(null);
  const [toggling, setToggling] = useState(false);
  const [toggleError, setToggleError] = useState("");
  const [toggleSuccess, setToggleSuccess] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    getSettings()
      .then(data => {
        setSettings(data);
        setError(null);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [getSettings, settingsVersion]);

  useEffect(() => { load(); }, [load]);

  const handleMaintenanceConfirm = async () => {
    if (confirmTarget === null) return;
    setToggling(true);
    setToggleError("");
    try {
      const result = await updateMaintenanceMode(confirmTarget);
      setSettings(prev => prev ? { ...prev, maintenanceMode: result.maintenanceMode } : prev);
      invalidateSettings();
      setToggleSuccess(result.message || "Maintenance mode updated.");
      setTimeout(() => setToggleSuccess(""), 4000);
    } catch (err) {
      setToggleError(err.message || "Failed to update maintenance mode");
    } finally {
      setToggling(false);
      setConfirmTarget(null);
    }
  };

  const requestMaintenanceToggle = () => {
    if (!settings) return;
    setConfirmTarget(!settings.maintenanceMode);
  };

  if (error && !settings) {
    return <div className="admin-error-state">Failed to load settings: {error}</div>;
  }

  const maintenanceOn = settings?.maintenanceMode === true;

  return (
    <div className="admin-settings-page">
      <h1 className="admin-page-title">System Settings</h1>

      {error && <div className="admin-error-state" style={{ height: "auto", marginBottom: 16 }}>{error}</div>}
      {toggleSuccess && <div className="admin-success-banner">{toggleSuccess}</div>}
      {toggleError && <p className="admin-inline-error" style={{ marginBottom: 16 }}>{toggleError}</p>}

      <div className="admin-stats-grid admin-stats-grid-2">
        <StatCard
          icon={<Package size={20} />}
          label="App Version"
          value={settings?.appVersion ?? "—"}
          accent="#6366f1"
        />
        <StatCard
          icon={<Wrench size={20} />}
          label="Maintenance Mode"
          value={maintenanceOn ? "Enabled" : "Disabled"}
          accent={maintenanceOn ? "#ef4444" : "#10b981"}
        />
      </div>

      <div className={`admin-settings-grid ${loading ? "admin-table-updating" : ""}`}>
        <div className="admin-form-card">
          <h3 className="admin-chart-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Cpu size={16} /> Judge0 API
          </h3>
          <SettingRow icon={<Key size={14} />} label="API Key" value={settings?.judge0ApiKeyMasked} mono />
          <SettingRow icon={<Link2 size={14} />} label="API URL" value={settings?.judge0ApiUrl} mono />
        </div>

        <div className="admin-form-card">
          <h3 className="admin-chart-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Sparkles size={16} /> Groq API
          </h3>
          <SettingRow icon={<Key size={14} />} label="API Key" value={settings?.groqApiKeyMasked} mono />
          <SettingRow icon={<Link2 size={14} />} label="API URL" value={settings?.groqApiUrl} mono />
        </div>
      </div>

      <div className={`admin-form-card admin-maintenance-card ${loading ? "admin-table-updating" : ""}`}>
        <div className="admin-maintenance-header">
          <div>
            <h3 className="admin-chart-title" style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <Settings size={16} /> Maintenance Mode
            </h3>
            <p className="admin-maintenance-desc">
              When enabled, non-admin users receive a 503 response and cannot use the platform.
              Admin routes remain accessible.
            </p>
          </div>
          <div className="admin-maintenance-status">
            <span className={`admin-maintenance-badge ${maintenanceOn ? "on" : "off"}`}>
              {maintenanceOn ? "ACTIVE" : "INACTIVE"}
            </span>
            <button
              type="button"
              className={maintenanceOn ? "admin-btn-secondary" : "admin-btn-danger"}
              onClick={requestMaintenanceToggle}
              disabled={toggling || !settings}
            >
              {toggling
                ? "Updating..."
                : maintenanceOn
                  ? "Disable Maintenance"
                  : "Enable Maintenance"}
            </button>
          </div>
        </div>

        {maintenanceOn && (
          <div className="admin-maintenance-warning">
            <AlertTriangle size={16} />
            <span>Platform is currently in maintenance mode. Regular users are blocked.</span>
          </div>
        )}
      </div>

      {confirmTarget !== null && (
        <ConfirmModal
          title={confirmTarget ? "Enable Maintenance Mode?" : "Disable Maintenance Mode?"}
          message={
            confirmTarget
              ? "This will block all non-admin users from accessing the platform. Are you sure?"
              : "This will restore normal access for all users. Continue?"
          }
          confirmLabel={confirmTarget ? "Enable" : "Disable"}
          danger={confirmTarget}
          onConfirm={handleMaintenanceConfirm}
          onCancel={() => setConfirmTarget(null)}
        />
      )}
    </div>
  );
}
