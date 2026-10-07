import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const API = "http://127.0.0.1:8001";

function App() {
  const navigate = useNavigate();

  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        const response = await axios.post(
          `${API}/auth/login`,
          {
            email,
            password,
          }
        );

        localStorage.setItem(
          "token",
          response.data.access_token
        );

        alert("Login successful!");
        navigate("/events");
      } else {
        await axios.post(
          `${API}/auth/register`,
          {
            username,
            email,
            password,
          }
        );

        alert(
          "Registration successful! Please login."
        );

        setIsLogin(true);
        setUsername("");
        setEmail("");
        setPassword("");
      }
    } catch (error) {
      console.error(error);

      alert(
        error.response?.data?.detail ||
          "Something went wrong"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">

      <div className="auth-left">

        <div className="auth-brand">
          🎟️ SmartEvent
        </div>

        <div className="auth-intro">
          <h1>
            Discover.
            <br />
            Book.
            <br />
            Experience.
          </h1>

          <p>
            Find the best events around you and
            book your tickets in just a few clicks.
          </p>
        </div>

      </div>

      <div className="auth-right">

        <div className="auth-box">

          <div className="auth-icon">
            🎟️
          </div>

          <h1>
            {isLogin
              ? "Welcome Back"
              : "Create Account"}
          </h1>

          <p className="auth-subtitle">
            {isLogin
              ? "Login to continue to SmartEvent"
              : "Join SmartEvent and discover amazing events"}
          </p>

          <form onSubmit={handleSubmit}>

            {!isLogin && (
              <div className="input-group">
                <label>Username</label>

                <input
                  type="text"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) =>
                    setUsername(e.target.value)
                  }
                  required
                />
              </div>
            )}

            <div className="input-group">
              <label>Email</label>

              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) =>
                  setEmail(e.target.value)
                }
                required
              />
            </div>

            <div className="input-group">
              <label>Password</label>

              <input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) =>
                  setPassword(e.target.value)
                }
                required
              />
            </div>

            <button
              type="submit"
              className="auth-submit"
              disabled={loading}
            >
              {loading
                ? "Please wait..."
                : isLogin
                ? "Login"
                : "Create Account"}
            </button>

          </form>

          <div className="auth-switch">

            <span>
              {isLogin
                ? "Don't have an account?"
                : "Already have an account?"}
            </span>

            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setUsername("");
                setEmail("");
                setPassword("");
              }}
            >
              {isLogin
                ? "Create Account"
                : "Login"}
            </button>

          </div>

        </div>

      </div>

    </div>
  );
}

export default App;