
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";

export default function Wishlist() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadWishlist = async () => {
    try {
      const response = await api.get("/wishlist");
      setItems(response.data);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not load wishlist.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWishlist();
  }, []);

  const removeItem = async (eventId) => {
    try {
      await api.delete(`/wishlist/${eventId}`);
      setItems((previous) =>
        previous.filter((item) => item.event_id !== eventId)
      );
    } catch (err) {
      setError(err.response?.data?.detail || "Could not remove event.");
    }
  };

  if (loading) return <p>Loading wishlist...</p>;

  return (
    <div className="page-container">
      <h1>My Wishlist ❤️</h1>

      {error && <p role="alert">{error}</p>}

      {items.length === 0 ? (
        <p>Your wishlist is empty.</p>
      ) : (
        <div className="events-grid">
          {items.map((item) => {
            const event = item.event;

            return (
              <article className="event-card" key={item.id}>
                <h2>{event?.title || `Event #${item.event_id}`}</h2>
                {event && (
                  <>
                    <p>{event.description}</p>
                    <p>📍 {event.location}</p>
                    <p>Price: ₹{event.ticket_price}</p>
                    <p>Available tickets: {event.available_tickets}</p>
                    <Link to={`/events/${event.id}`}>
                      View event / Book
                    </Link>
                  </>
                )}
                <button onClick={() => removeItem(item.event_id)}>
                  Remove from wishlist
                </button>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
