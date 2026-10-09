import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const API = "http://127.0.0.1:8001";

function AdminDashboard() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [users, setUsers] = useState([]);
  const [events, setEvents] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const headers = useCallback(() => ({
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  }), []);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const config = { headers: headers() };
      const me = await axios.get(`${API}/auth/me`, config);
      if (me.data.role !== "ADMIN") {
        navigate("/events", { replace: true });
        return;
      }
      setProfile(me.data);

      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const [stats, userResponse, eventResponse, bookingResponse] = await Promise.all([
        axios.get(`${API}/admin/analytics`, { ...config, params }),
        axios.get(`${API}/admin/users`, config),
        axios.get(`${API}/admin/events`, config),
        axios.get(`${API}/admin/bookings`, { ...config, params }),
      ]);
      setAnalytics(stats.data);
      setUsers(userResponse.data);
      setEvents(eventResponse.data);
      setBookings(bookingResponse.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not load admin dashboard. Verify the backend and ADMIN role.");
    } finally {
      setLoading(false);
    }
  }, [headers, navigate, startDate, endDate]);

  useEffect(() => { loadData(); }, [loadData]);

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  if (loading) return <div className="dashboard-page"><p>Loading admin dashboard...</p></div>;

  const totals = analytics?.totals || {};
  return (
    <div className="dashboard-page">
      <header className="dashboard-topbar">
        <div><strong>🎟️ SmartEvent</strong><span>Administration</span></div>
        <div className="dashboard-actions">
          <span>{profile?.username} · ADMIN</span>
          <button className="secondary-button" onClick={() => navigate("/events")}>Browse events</button>
          <button className="danger-button" onClick={logout}>Logout</button>
        </div>
      </header>

      <main className="dashboard-container">
        <div className="dashboard-heading">
          <div><p className="eyebrow">ADMIN PORTAL</p><h1>Platform overview</h1><p>Monitor users, events, bookings, ticket sales and revenue.</p></div>
          <button className="secondary-button" onClick={loadData}>Refresh</button>
        </div>

        {error && <div className="dashboard-alert error-alert">{String(error)}</div>}

        <section className="dashboard-panel">
          <div className="panel-heading"><div><h2>Analytics date filter</h2><p>Leave dates blank to show all booking history.</p></div></div>
          <div className="filter-row">
            <label>Start date<input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} /></label>
            <label>End date<input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} /></label>
            <button className="primary-button" onClick={loadData}>Apply filter</button>
            <button className="secondary-button" onClick={() => { setStartDate(""); setEndDate(""); }}>Clear</button>
          </div>
        </section>

        <section className="metric-grid">
          <Metric label="Total users" value={totals.users ?? 0} />
          <Metric label="Total events" value={totals.events ?? 0} />
          <Metric label="Confirmed bookings" value={totals.bookings ?? 0} />
          <Metric label="Tickets sold" value={totals.tickets_sold ?? 0} />
          <Metric label="Revenue" value={`₹${totals.revenue ?? 0}`} />
        </section>

        <section className="dashboard-panel">
          <div className="panel-heading"><div><h2>Daily ticket sales</h2><p>Based on the selected booking date range.</p></div></div>
          {(analytics?.daily_ticket_sales || []).length === 0 ? <p className="empty-state">No sales in this date range.</p> : (
            <div className="table-wrap"><table className="dashboard-table">
              <thead><tr><th>Date</th><th>Tickets sold</th><th>Bookings</th><th>Revenue</th></tr></thead>
              <tbody>{analytics.daily_ticket_sales.map((row) => <tr key={row.date}><td>{row.date}</td><td>{row.tickets_sold}</td><td>{row.bookings}</td><td>₹{row.revenue}</td></tr>)}</tbody>
            </table></div>
          )}
        </section>

        <section className="dashboard-panel">
          <div className="panel-heading"><div><h2>Monthly booking trends</h2><p>Monthly booking count and revenue.</p></div></div>
          {(analytics?.monthly_booking_trends || []).length === 0 ? <p className="empty-state">No monthly booking data.</p> : (
            <div className="table-wrap"><table className="dashboard-table">
              <thead><tr><th>Month</th><th>Bookings</th><th>Revenue</th></tr></thead>
              <tbody>{analytics.monthly_booking_trends.map((row) => <tr key={row.month}><td>{row.month}</td><td>{row.bookings}</td><td>₹{row.revenue}</td></tr>)}</tbody>
            </table></div>
          )}
        </section>

        <section className="dashboard-panel">
          <div className="panel-heading"><div><h2>Popular events</h2><p>Ranked by tickets sold.</p></div></div>
          <DataTable columns={["Event", "Tickets sold", "Bookings", "Revenue"]} rows={(analytics?.popular_events || []).map((r) => [r.title, r.tickets_sold, r.bookings, `₹${r.revenue}`])} />
        </section>

        <section className="dashboard-panel">
          <div className="panel-heading"><div><h2>Top revenue events</h2><p>Ranked by confirmed booking revenue.</p></div></div>
          <DataTable columns={["Event", "Revenue", "Tickets sold", "Bookings"]} rows={(analytics?.top_revenue_events || []).map((r) => [r.title, `₹${r.revenue}`, r.tickets_sold, r.bookings])} />
        </section>

        <section className="dashboard-panel">
          <div className="panel-heading"><div><h2>Users</h2><p>{users.length} registered accounts.</p></div></div>
          <DataTable columns={["ID", "Username", "Email", "Role", "Created"]} rows={users.map((u) => [u.id, u.username, u.email, u.role, u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"])} />
        </section>

        <section className="dashboard-panel">
          <div className="panel-heading"><div><h2>Events</h2><p>{events.length} events across all organizers.</p></div></div>
          <DataTable columns={["ID", "Title", "Organizer ID", "Status", "Date", "Available"]} rows={events.map((e) => [e.id, e.title, e.organizer_id ?? "—", e.event_status, new Date(e.event_date).toLocaleString(), `${e.available_tickets}/${e.total_tickets}`])} />
        </section>

        <section className="dashboard-panel">
          <div className="panel-heading"><div><h2>Bookings</h2><p>{bookings.length} booking records in the selected date range.</p></div></div>
          <DataTable columns={["ID", "User ID", "Event ID", "Tickets", "Amount", "Status", "Date"]} rows={bookings.map((b) => [b.id, b.user_id, b.event_id, b.ticket_count, `₹${b.total_amount}`, b.status, new Date(b.booking_date).toLocaleString()])} />
        </section>
      </main>
    </div>
  );
}

function Metric({ label, value }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong></div>;
}

function DataTable({ columns, rows }) {
  if (!rows.length) return <p className="empty-state">No records to display.</p>;
  return <div className="table-wrap"><table className="dashboard-table">
    <thead><tr>{columns.map((col) => <th key={col}>{col}</th>)}</tr></thead>
    <tbody>{rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{cell ?? "—"}</td>)}</tr>)}</tbody>
  </table></div>;
}

export default AdminDashboard;
