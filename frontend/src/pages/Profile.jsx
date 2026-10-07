import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";

const API = "http://127.0.0.1:8001";

function Profile() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProfile = async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        navigate("/");
        return;
      }

      try {
        const response = await axios.get(
          `${API}/auth/me`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        setUser(response.data);
      } catch (error) {
        console.error(error);

        if (error.response?.status === 401) {
          localStorage.removeItem("token");
          navigate("/");
        } else {
          alert("Unable to load profile");
        }
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, [navigate]);

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="profile-loading">
          Loading profile...
        </div>
      </>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <>
      <Navbar />

      <div className="profile-page">

        <div className="profile-card">

          <div className="profile-avatar">
            {user.username.charAt(0).toUpperCase()}
          </div>

          <h1>{user.username}</h1>

          <p className="profile-subtitle">
            SmartEvent Member
          </p>

          <div className="profile-info">

            <div className="profile-item">
              <span>👤 Username</span>
              <strong>{user.username}</strong>
            </div>

            <div className="profile-item">
              <span>📧 Email</span>
              <strong>{user.email}</strong>
            </div>

            <div className="profile-item">
              <span>🆔 User ID</span>
              <strong>#{user.id}</strong>
            </div>

          </div>

          <button
            className="profile-events-button"
            onClick={() => navigate("/events")}
          >
            🎟️ Discover Events
          </button>

          <button
            className="profile-logout-button"
            onClick={() => {
              localStorage.removeItem("token");
              navigate("/");
            }}
          >
            Logout
          </button>

        </div>

      </div>
    </>
  );
}

export default Profile;