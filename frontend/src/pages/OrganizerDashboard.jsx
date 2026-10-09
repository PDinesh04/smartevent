import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const API = "http://127.0.0.1:8001";
const emptyForm = {
  title: "", description: "", category: "", location: "",
  event_date: "", ticket_price: 0, total_tickets: 100, banner_image: ""
};

function OrganizerDashboard() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [events, setEvents] = useState([]);
  const [analytics, setAnalytics] = useState({ events: [], totals: {} });
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const headers = useCallback(() => ({
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  }), []);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const config = { headers: headers() };
      const [me, eventResponse, stats] = await Promise.all([
        axios.get(`${API}/auth/me`, config),
        axios.get(`${API}/organizer/events`, config),
        axios.get(`${API}/organizer/analytics`, config),
      ]);
      if (!["ORGANIZER", "ADMIN"].includes(me.data.role)) {
        navigate("/events", { replace: true });
        return;
      }
      setProfile(me.data);
      setEvents(eventResponse.data);
      setAnalytics(stats.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not load organizer dashboard. Check that the backend is running and you have ORGANIZER role.");
    } finally {
      setLoading(false);
    }
  }, [headers, navigate]);

  useEffect(() => { loadData(); }, [loadData]);

  const setField = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  const submitEvent = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      const payload = {
        ...form,
        event_date: new Date(form.event_date).toISOString(),
        ticket_price: Number(form.ticket_price),
        total_tickets: Number(form.total_tickets),
        banner_image: form.banner_image.trim() || null,
      };
      if (editingId) {
        await axios.put(`${API}/events/${editingId}`, payload, { headers: headers() });
        setMessage("Event updated successfully.");
      } else {
        await axios.post(`${API}/events`, payload, { headers: headers() });
        setMessage("Event created successfully.");
      }
      setForm(emptyForm);
      setEditingId(null);
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to save event.");
    }
  };

  const beginEdit = (event) => {
    setEditingId(event.id);
    setForm({
      title: event.title || "",
      description: event.description || "",
      category: event.category || "",
      location: event.location || "",
      event_date: event.event_date ? new Date(event.event_date).toISOString().slice(0, 16) : "",
      ticket_price: event.ticket_price ?? 0,
      total_tickets: event.total_tickets ?? 100,
      banner_image: event.banner_image || "",
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const cancelEvent = async (event) => {
    if (!window.confirm(`Cancel "${event.title}"? Booked users will be notified.`)) return;
    setError("");
    setMessage("");
    try {
      await axios.post(`${API}/events/${event.id}/cancel`, {}, { headers: headers() });
      setMessage("Event cancelled. Booked users have been notified.");
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to cancel event.");
    }
  };

  const showBookings = async (event) => {
    try {
      const response = await axios.get(`${API}/organizer/events/${event.id}/bookings`, { headers: headers() });
      const data = response.data;
      window.alert(
        `${data.event_title}\nBookings: ${data.booking_count}\nTickets sold: ${data.tickets_sold}\nRevenue: ₹${data.revenue}\n\n` +
        (data.bookings || []).map((b) => `Booking #${b.id}: ${b.ticket_count} tickets, ₹${b.total_amount}, ${b.status}`).join("\n")
      );
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to load event bookings.");
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  if (loading) return <div className="dashboard-page"><p>Loading organizer dashboard...</p></div>;

  return (
    <div className="dashboard-page">
      <header className="dashboard-topbar">
        <div><strong>🎟️ SmartEvent</strong><span>Organizer workspace</span></div>
        <div className="dashboard-actions">
          <span>{profile?.username} · {profile?.role}</span>
          <button className="secondary-button" onClick={() => navigate("/events")}>Browse events</button>
          <button className="danger-button" onClick={logout}>Logout</button>
        </div>
      </header>

      <main className="dashboard-container">
        <div className="dashboard-heading">
          <div><p className="eyebrow">ORGANIZER PORTAL</p><h1>Event management</h1><p>Create events, manage ticket availability and monitor sales.</p></div>
          <button className="secondary-button" onClick={loadData}>Refresh data</button>
        </div>

        {error && <div className="dashboard-alert error-alert">{String(error)}</div>}
        {message && <div className="dashboard-alert success-alert">{message}</div>}

        <section className="metric-grid">
          <Metric label="Your events" value={analytics.totals?.events ?? events.length} />
          <Metric label="Tickets sold" value={analytics.totals?.tickets_sold ?? 0} />
          <Metric label="Bookings" value={analytics.totals?.booking_count ?? 0} />
          <Metric label="Revenue" value={`₹${analytics.totals?.revenue ?? 0}`} />
        </section>

        <section className="dashboard-panel">
          <div className="panel-heading"><div><h2>{editingId ? "Edit event" : "Create an event"}</h2><p>Fields marked required must be filled in.</p></div></div>
          <form className="event-form-grid" onSubmit={submitEvent}>
            <label>Event title<input required maxLength="200" value={form.title} onChange={(e) => setField("title", e.target.value)} /></label>
            <label>Category<input required value={form.category} onChange={(e) => setField("category", e.target.value)} /></label>
            <label>Location<input required value={form.location} onChange={(e) => setField("location", e.target.value)} /></label>
            <label>Event date and time<input required type="datetime-local" value={form.event_date} onChange={(e) => setField("event_date", e.target.value)} /></label>
            <label>Ticket price (₹)<input required min="0" type="number" value={form.ticket_price} onChange={(e) => setField("ticket_price", e.target.value)} /></label>
            <label>Total tickets<input required min="1" type="number" value={form.total_tickets} onChange={(e) => setField("total_tickets", e.target.value)} /></label>
            <label className="wide-field">Banner image URL (optional)<input value={form.banner_image} onChange={(e) => setField("banner_image", e.target.value)} /></label>
            <label className="wide-field">Description<textarea required rows="3" value={form.description} onChange={(e) => setField("description", e.target.value)} /></label>
            <div className="form-actions wide-field">
              <button className="primary-button" type="submit">{editingId ? "Save changes" : "Create event"}</button>
              {editingId && <button className="secondary-button" type="button" onClick={() => { setEditingId(null); setForm(emptyForm); }}>Stop editing</button>}
            </div>
          </form>
        </section>

        <section className="dashboard-panel">
          <div className="panel-heading"><div><h2>Manage events</h2><p>Update, cancel and inspect booking performance.</p></div><span className="count-pill">{events.length} events</span></div>
          {events.length === 0 ? <p className="empty-state">No events yet. Use the form above to create your first event.</p> : (
            <div className="table-wrap"><table className="dashboard-table">
              <thead><tr><th>Event</th><th>Date</th><th>Status</th><th>Tickets left</th><th>Price</th><th>Actions</th></tr></thead>
              <tbody>{events.map((event) => (
                <tr key={event.id}>
                  <td><strong>{event.title}</strong><small>{event.location}</small></td>
                  <td>{new Date(event.event_date).toLocaleString()}</td>
                  <td><span className={`status-pill ${String(event.event_status).toLowerCase()}`}>{event.event_status}</span></td>
                  <td>{event.available_tickets} / {event.total_tickets}</td>
                  <td>₹{event.ticket_price}</td>
                  <td><div className="table-actions">
                    <button className="small-button" onClick={() => showBookings(event)}>Bookings</button>
                    <button className="small-button" disabled={event.event_status === "CANCELLED"} onClick={() => beginEdit(event)}>Edit</button>
                    <button className="small-button danger-text" disabled={event.event_status === "CANCELLED"} onClick={() => cancelEvent(event)}>Cancel</button>
                  </div></td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </section>

        <section className="dashboard-panel">
          <div className="panel-heading"><div><h2>Event insights</h2><p>Ticket sales and revenue per event.</p></div></div>
          <div className="table-wrap"><table className="dashboard-table">
            <thead><tr><th>Event</th><th>Status</th><th>Bookings</th><th>Sold</th><th>Remaining</th><th>Revenue</th></tr></thead>
            <tbody>{(analytics.events || []).map((item) => <tr key={item.event_id}>
              <td>{item.title}</td><td>{item.event_status}</td><td>{item.booking_count}</td><td>{item.tickets_sold}</td><td>{item.tickets_remaining}</td><td>₹{item.revenue}</td>
            </tr>)}</tbody>
          </table></div>
        </section>
      </main>
    </div>
  );
}

function Metric({ label, value }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong></div>;
}

export default OrganizerDashboard;
