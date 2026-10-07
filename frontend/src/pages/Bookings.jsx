import { useEffect, useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";

function Bookings() {
  const navigate = useNavigate();

  const [bookings, setBookings] = useState([]);
  const [events, setEvents] = useState({});
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      navigate("/");
      return;
    }

    try {
      const bookingResponse = await api.get(
        "/bookings"
      );

      setBookings(bookingResponse.data);

      const eventData = {};

      for (const booking of bookingResponse.data) {
        try {
          const response = await api.get(
            `/events/${booking.event_id}`
          );

          eventData[booking.event_id] =
            response.data;
        } catch (error) {
          console.error(
            `Unable to load event ${booking.event_id}`,
            error
          );
        }
      }

      setEvents(eventData);

    } catch (error) {
      console.error(error);

      if (error.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/");
      } else {
        alert("Unable to load bookings");
      }

    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const showQR = async (bookingId) => {
    try {
      const response = await api.get(
        `/bookings/${bookingId}/qr`,
        {
          responseType: "blob",
        }
      );

      const imageUrl = URL.createObjectURL(
        response.data
      );

      window.open(imageUrl, "_blank");

    } catch (error) {
      console.error(error);
      alert("Unable to generate QR ticket");
    }
  };

  if (loading) {
    return (
      <>
        <Navbar />

        <div className="bookings-loading">
          Loading your bookings...
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />

      <div className="bookings-page">

        <div className="bookings-header">
          <h1>My Bookings</h1>

          <p>
            View and manage all your SmartEvent tickets.
          </p>
        </div>

        {bookings.length === 0 ? (

          <div className="empty-bookings">

            <div className="empty-icon">
              🎟️
            </div>

            <h2>No bookings yet</h2>

            <p>
              You haven't booked any events yet.
            </p>

            <button
              onClick={() => navigate("/events")}
            >
              Discover Events
            </button>

          </div>

        ) : (

          <div className="bookings-list">

            {bookings.map((booking) => {

              const event =
                events[booking.event_id];

              return (
                <div
                  className="booking-card"
                  key={booking.id}
                >

                  {event?.banner_image ? (

                    <img
                      src={event.banner_image}
                      alt={event.title}
                      className="booking-image"
                    />

                  ) : (

                    <div className="booking-image-placeholder">
                      🎫
                    </div>

                  )}

                  <div className="booking-content">

                    <div className="booking-top">

                      <div>

                        <span className="booking-category">
                          {event?.category || "Event"}
                        </span>

                        <h2>
                          {event
                            ? event.title
                            : `Event #${booking.event_id}`}
                        </h2>

                      </div>

                      <span
                        className={`booking-status ${
                          booking.status === "CONFIRMED"
                            ? "confirmed"
                            : "cancelled"
                        }`}
                      >
                        {booking.status}
                      </span>

                    </div>

                    {event && (
                      <div className="booking-event-info">

                        <p>
                          📍 {event.location}
                        </p>

                        <p>
                          📅{" "}
                          {new Date(
                            event.event_date
                          ).toLocaleString()}
                        </p>

                      </div>
                    )}

                    <div className="booking-details">

                      <div>
                        <span>Booking ID</span>
                        <strong>
                          #{booking.id}
                        </strong>
                      </div>

                      <div>
                        <span>Tickets</span>
                        <strong>
                          {booking.ticket_count}
                        </strong>
                      </div>

                      <div>
                        <span>Total Amount</span>
                        <strong>
                          ₹{booking.total_amount}
                        </strong>
                      </div>

                      <div>
                        <span>Booked On</span>
                        <strong>
                          {new Date(
                            booking.booking_date
                          ).toLocaleDateString()}
                        </strong>
                      </div>

                    </div>

                    <div className="booking-actions">

                      <button
                        className="qr-button"
                        onClick={() =>
                          showQR(booking.id)
                        }
                      >
                        🎟️ View QR Ticket
                      </button>

                      {event && (
                        <button
                          className="details-button"
                          onClick={() =>
                            navigate(
                              `/events/${event.id}`
                            )
                          }
                        >
                          View Event
                        </button>
                      )}

                    </div>

                  </div>

                </div>
              );
            })}

          </div>
        )}

      </div>
    </>
  );
}

export default Bookings;