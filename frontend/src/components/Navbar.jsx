import { NavLink, useNavigate } from "react-router-dom";

function Navbar() {
  const navigate = useNavigate();

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  const linkClass = ({ isActive }) =>
    `nav-link ${isActive ? "active" : ""}`;

  return (
    <nav className="navbar">

      <div
        className="navbar-brand"
        onClick={() => navigate("/events")}
      >
        <span className="brand-icon">🎟️</span>
        <span>SmartEvent</span>
      </div>

      <div className="navbar-links">

        <NavLink
          to="/events"
          className={linkClass}
        >
          Events
        </NavLink>

        <NavLink
          to="/bookings"
          className={linkClass}
        >
          My Bookings
        </NavLink>

        <NavLink
          to="/notifications"
          className={linkClass}
        >
          🔔 Notifications
        </NavLink>

        <NavLink
          to="/profile"
          className={linkClass}
        >
          👤 Profile
        </NavLink>

      </div>

      <button
        className="logout-button"
        onClick={logout}
      >
        Logout
      </button>

    </nav>
  );
}

export default Navbar;