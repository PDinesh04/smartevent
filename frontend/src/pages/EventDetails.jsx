import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api";
import Navbar from "../components/Navbar";

function EventDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [event, setEvent] = useState(null);
  const [tickets, setTickets] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadEvent = async () => {
      try {
        const response = await api.get(
          `/events/${id}`
        );

        setEvent(response.data);
      } catch (error) {
        console.error(error);
        alert("Unable to load event");
      } finally {
        setLoading(false);
      }
    };

    loadEvent();
  }, [id]);

  const bookTickets = async () => {
    if (!localStorage.getItem("token")) {
      alert("Please login first");
      navigate("/");
      return;
    }

    if (
      Number(tickets) < 1 ||
      Number(tickets) > event.available_tickets
    ) {
      alert("Invalid ticket quantity");
      return;
    }

    try {
      await api.post("/bookings", {
        event_id: Number(id),
        ticket_count: Number(tickets),
      });

      alert("Booking successful!");

      navigate("/bookings");
    } catch (error) {
      console.error(error);

      alert(
        error.response?.data?.detail ||
          "Booking failed"
      );
    }
  };

  if (loading) {
    return (
      <>
        <Navbar />

        <div className="details-loading">
          Loading event...
        </div>
      </>
    );
  }

  if (!event) {
    return (
      <>
        <Navbar />

        <div className="details-loading">
          Event not found
        </div>
      </>
    );
  }

  const totalPrice =
    event.ticket_price * Number(tickets || 0);

  return (
    <>
      <Navbar />

      <div className="details-page">

        <button
          className="back-button"
          onClick={() => navigate("/events")}
        >
          ← Back to Events
        </button>

        <div className="details-card">

          {event.banner_image ? (
            <img
              src={event.banner_image}
              alt={event.title}
              className="details-banner"
            />
          ) : (
            <div className="details-banner-placeholder">
              🎫
            </div>
          )}

          <div className="details-content">

            <span className="event-category">
              {event.category}
            </span>

            <h1>{event.title}</h1>

            <p className="details-description">
              {event.description}
            </p>

            <div className="details-info">

              <div className="info-box">
                <span>📍</span>

                <div>
                  <small>Location</small>
                  <strong>
                    {event.location}
                  </strong>
                </div>
              </div>

              <div className="info-box">
                <span>📅</span>

                <div>
                  <small>Date & Time</small>

                  <strong>
                    {new Date(
                      event.event_date
                    ).toLocaleString()}
                  </strong>
                </div>
              </div>

              <div className="info-box">
                <span>🎟️</span>

                <div>
                  <small>
                    Available Tickets
                  </small>

                  <strong>
                    {event.available_tickets}
                  </strong>
                </div>
              </div>

              <div className="info-box">
                <span>💰</span>

                <div>
                  <small>Ticket Price</small>

                  <strong>
                    ₹{event.ticket_price}
                  </strong>
                </div>
              </div>

            </div>

            <div className="booking-section">

              <h2>
                Book Your Tickets
              </h2>

              <div className="booking-row">

                <div>
                  <label>
                    Number of Tickets
                  </label>

                  <input
                    type="number"
                    min="1"
                    max={event.available_tickets}
                    value={tickets}
                    onChange={(e) =>
                      setTickets(e.target.value)
                    }
                  />
                </div>

                <div className="total-price">

                  <span>
                    Total Amount
                  </span>

                  <strong>
                    ₹{totalPrice}
                  </strong>

                </div>

                <button
                  className="book-button"
                  onClick={bookTickets}
                  disabled={
                    event.available_tickets === 0
                  }
                >
                  {event.available_tickets === 0
                    ? "Sold Out"
                    : "Book Tickets"}
                </button>

              </div>

            </div>

          </div>

        </div>

      </div>
    </>
  );
}

export default EventDetails;