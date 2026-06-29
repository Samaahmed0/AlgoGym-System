import React, { useState, useEffect, useCallback } from "react";
import "../styles/Profile.css";
import { FiUser, FiMail, FiGithub } from "react-icons/fi";
import DefaultAvatar from '../utils/profile.jpg';
import { compressImage, isImageFile } from "../utils/compressImage";
import { useToast } from "../components/ToastProvider";
import { updateUser } from "../api/user.api";
import { useUserData } from "../UserDataContext";

function Profile() {
  const { showToast } = useToast();
  const { getProfile, invalidateProfile, profileVersion } = useUserData();

  const [userId, setUserId] = useState(null);
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [bio, setBio] = useState("");
  const [github, setGithub] = useState("");
  const [avatar, setAvatar] = useState(DefaultAvatar);
  const [avatarDirty, setAvatarDirty] = useState(false);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    getProfile()
      .then(user => {
        setUserId(user.id);
        setDisplayName(user.username ?? "");
        setEmail(user.email ?? "");
        setBio(user.bio ?? "");
        setGithub(user.githubUrl ?? "");
        setAvatar(user.avatarUrl ?? DefaultAvatar);
        setAvatarDirty(false);
        setError(null);
      })
      .catch(err => {
        console.error("Failed to load user:", err);
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, [getProfile, profileVersion]);

  useEffect(() => { load(); }, [load]);

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    if (!isImageFile(file)) {
      showToast("Please select an image file (PNG, JPG, etc.).");
      return;
    }

    setAvatarUploading(true);
    try {
      const dataUrl = await compressImage(file);
      setAvatar(dataUrl);
      setAvatarDirty(true);
    } catch (err) {
      console.error(err);
      showToast(err.message || "Could not process that image.");
    } finally {
      setAvatarUploading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        username: displayName,
        email,
        bio,
        githubUrl: github,
      };
      if (avatarDirty && avatar.startsWith("data:image/")) {
        payload.avatarUrl = avatar;
      }
      await updateUser(userId, payload);
      setAvatarDirty(false);
      invalidateProfile();
      showToast("Changes saved!");
    } catch (err) {
      console.error(err);
      showToast(err.message || "Failed to save changes.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="profile-content">
      {loading && !userId && (
        <div className="loader-container">
          <div className="modern-spinner"></div>
          <p>LOADING_PROFILE...</p>
        </div>
      )}

      {error && !userId && (
        <div className="loader-container">
          <p style={{ color: "#dc2626" }}>{error}</p>
        </div>
      )}

      {userId && (
        <div className={`profile-card ${loading ? "profile-card-updating" : ""}`}>
          <div className="profile-header">
            <label htmlFor="avatar-upload" className={`avatar-label ${avatarUploading ? "avatar-label-busy" : ""}`}>
              <img src={avatar} alt="Profile" className="avatar" />
              {avatarUploading && <span className="avatar-upload-overlay">Processing…</span>}
              <input
                type="file"
                id="avatar-upload"
                accept="image/*"
                style={{ display: "none" }}
                disabled={avatarUploading || saving}
                onChange={handleAvatarChange}
              />
            </label>
          </div>

          <div className="profile-info">
            <h2>{displayName}</h2>
          </div>

          <form className="profile-form" onSubmit={handleSave}>
            <div className="form-row">
              <div className="form-group">
                <label>Username</label>
                <div className="input-group">
                  <FiUser className="input-icon" />
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Email</label>
                <div className="input-group">
                  <FiMail className="input-icon" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group bio-group">
                <label>Bio</label>
                <textarea
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  rows="4"
                ></textarea>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>GitHub</label>
                <div className="input-group">
                  <FiGithub className="input-icon" />
                  <input
                    type="text"
                    value={github}
                    onChange={(e) => setGithub(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <button type="submit" className="save-btn" disabled={saving || avatarUploading}>
              {saving ? "Saving…" : "Save Changes"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

export default Profile;
