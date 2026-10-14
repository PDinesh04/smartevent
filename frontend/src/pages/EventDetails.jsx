
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
  const [couponCode, setCouponCode] = useState("");
  const [appliedCoupon, setAppliedCoupon] = useState(null);
  const [couponError, setCouponError] = useState("");
  const [couponLoading, setCouponLoading] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [availabilityUpdated, setAvailabilityUpdated] = useState(false);

  const [reviews, setReviews] = useState([]);
  const [averageRating, setAverageRating] = useState(0);
  const [reviewText, setReviewText] = useState("");
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewMessage, setReviewMessage] = useState("");

  useEffect(() => {
    const loadEvent = async () => {
      try {
        const response = await api.get(`/events/${id}`);
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


  useEffect(() => {
  const refreshAvailability = async () => {
    try {
      const response = await api.get(`/events/${id}`);
      setEvent((previous) => {
        if (!previous) return response.data;
        return {
          ...previous,
          available_tickets: response.data.available_tickets,
        };
      });
      setAvailabilityUpdated(true);
    } catch (error) {
      console.error("Unable to refresh ticket availability", error);
    }
  };

  const intervalId = setInterval(refreshAvailability, 5000);

  return () => clearInterval(intervalId);
}, [id]);

  useEffect(() => {
    const loadReviews = async () => {
      try {
        const response = await api.get(`/events/${id}/reviews`);
        setReviews(response.data.reviews || []);
        setAverageRating(response.data.average_rating || 0);
      } catch (error) {
        console.error("Unable to load reviews", error);
      }
    };

    loadReviews();
  }, [id]);

  const quantity = Number(tickets);
  const totalPrice = event
    ? Number(event.ticket_price) * quantity
    : 0;

  const applyCoupon = async () => {
    if (
      !event ||
      !Number.isInteger(quantity) ||
      quantity < 1 ||
      quantity > event.available_tickets
    ) {
      setCouponError("Please select a valid ticket quantity first.");
      return;
    }

    try {
      setCouponLoading(true);
      setCouponError("");
      setAppliedCoupon(null);

      const response = await api.post("/coupons/validate", {
        coupon_code: couponCode.trim().toUpperCase(),
        amount: totalPrice,
      });

      setAppliedCoupon(response.data);
    } catch (error) {
      setCouponError(
        error.response?.data?.detail || "Unable to apply coupon"
      );
    } finally {
      setCouponLoading(false);
    }
  };

  const removeCoupon = () => {
    setAppliedCoupon(null);
    setCouponCode("");
    setCouponError("");
  };

  const bookTickets = async () => {
    if (!localStorage.getItem("token")) {
      alert("Please login first");
      navigate("/");
      return;
    }

    if (
      !Number.isInteger(quantity) ||
      quantity < 1 ||
      quantity > event.available_tickets
    ) {
      alert("Invalid ticket quantity");
      return;
    }

    try {
      setBookingLoading(true);

      const response = await api.post("/bookings/checkout", {
        event_id: Number(id),
        ticket_count: quantity,
        coupon_code: appliedCoupon?.coupon_code || null,
      });

      navigate(`/payment/${response.data.booking_id}`, {
        state: response.data,
      });
    } catch (error) {
      alert(error.response?.data?.detail || "Checkout failed");
    } finally {
      setBookingLoading(false);
    }
  };

  const submitReview = async (e) => {
    e.preventDefault();
    setReviewLoading(true);
    setReviewMessage("");

    try {
      await api.post(`/events/${id}/reviews`, {
        rating: reviewRating,
        comment: reviewText,
      });

      const response = await api.get(`/events/${id}/reviews`);
      setReviews(response.data.reviews || []);
      setAverageRating(response.data.average_rating || 0);
      setReviewText("");
      setReviewRating(5);
      setReviewMessage("Review submitted successfully!");
    } catch (error) {
      setReviewMessage(
        error.response?.data?.detail || "Unable to submit review"
      );
    } finally {
      setReviewLoading(false);
    }
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="details-loading">Loading event...</div>
      </>
    );
  }

  if (!event) {
    return (
      <>
        <Navbar />
        <div className="details-loading">Event not found</div>
      </>
    );
  }

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
            <div className="details-banner-placeholder">🎫</div>
          )}

          <div className="details-content">
            <span className="event-category">{event.category}</span>
            <h1>{event.title}</h1>
            <p className="details-description">{event.description}</p>

            <div className="details-info">
              <div className="info-box">
                <span>📍</span>
                <div>
                  <small>Location</small>
                  <strong>{event.location}</strong>
                </div>
              </div>

              <div className="info-box">
                <span>📅</span>
                <div>
                  <small>Date &amp; Time</small>
                  <strong>
                    {new Date(event.event_date).toLocaleString()}
                  </strong>
                </div>
              </div>

              <div className="info-box">
                <span>🎟️</span>
                <div>
                  <small>Available Tickets</small>
                  <strong>{event.available_tickets}</strong>
                </div>
              </div>

              <div className="info-box">
                <span>💰</span>
                <div>
                  <small>Ticket Price</small>
                  <strong>₹{event.ticket_price}</strong>
                </div>
              </div>
            </div>

            <div className="booking-section">
              <h2>Book Your Tickets</h2>

              <div className="booking-row">
                <div>
                  <label htmlFor="ticket-count">
                    Number of Tickets
                  </label>
                  <input
                    id="ticket-count"
                    type="number"
                    min="1"
                    max={event.available_tickets}
                    value={tickets}
                    onChange={(e) => {
                      setTickets(e.target.value);
                      setAppliedCoupon(null);
                      setCouponError("");
                    }}
                  />
                </div>

                <div className="total-price">
                  <span>Total Amount</span>
                  <strong>₹{totalPrice}</strong>
                </div>
              </div>

              <div className="coupon-section">
                <label htmlFor="coupon-code">Coupon code</label>

                <div className="coupon-input-row">
                  <input
                    id="coupon-code"
                    value={couponCode}
                    onChange={(e) => {
                      setCouponCode(e.target.value.toUpperCase());
                      setAppliedCoupon(null);
                      setCouponError("");
                    }}
                    placeholder="Enter coupon code"
                  />

                  <button
                    type="button"
                    onClick={applyCoupon}
                    disabled={!couponCode.trim() || couponLoading}
                  >
                    {couponLoading ? "Applying..." : "Apply"}
                  </button>
                </div>

                {couponError && (
                  <p className="coupon-error">{couponError}</p>
                )}

                {appliedCoupon && (
                  <div className="coupon-success">
                    <p>Coupon applied: {appliedCoupon.coupon_code}</p>
                    <p>Discount: ₹{appliedCoupon.discount_amount}</p>
                    <p>Final amount: ₹{appliedCoupon.final_amount}</p>
                    <button type="button" onClick={removeCoupon}>
                      Remove coupon
                    </button>
                  </div>
                )}
              </div>

              <button
                className="book-button"
                onClick={bookTickets}
                disabled={
                  bookingLoading ||
                  event.available_tickets === 0 ||
                  !Number.isInteger(quantity) ||
                  quantity < 1 ||
                  quantity > event.available_tickets
                }
              >
                {event.available_tickets === 0
                  ? "Sold Out"
                  : bookingLoading
                    ? "Processing..."
                    : "Proceed to Payment"}
              </button>
            </div>
          </div>
        </div>

        <section className="reviews-section">
          <h2>Event Reviews &amp; Ratings</h2>

          <p>
            Average rating: ⭐ {Number(averageRating).toFixed(1)} / 5
            {" "}({reviews.length} reviews)
          </p>

          <form onSubmit={submitReview}>
            <label>Choose your rating</label>

            <div className="star-rating">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setReviewRating(star)}
                  aria-label={`${star} star rating`}
                  aria-pressed={reviewRating === star}
                  style={{
                    color:
                      star <= reviewRating ? "#f59e0b" : "#9ca3af",
                    fontSize: "28px",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                  }}
                >
                  ★
                </button>
              ))}
            </div>

            <label htmlFor="review-text">Your review</label>
            <textarea
              id="review-text"
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
              maxLength={1000}
              placeholder="Share your experience..."
            />

            <button type="submit" disabled={reviewLoading}>
              {reviewLoading ? "Submitting..." : "Submit Review"}
            </button>

            {reviewMessage && <p role="status">{reviewMessage}</p>}
          </form>

          <div className="review-list">
            {reviews.map((review) => (
              <article key={review.id} className="review-card">
                <p>
                  {"★".repeat(review.rating)}
                  {"☆".repeat(5 - review.rating)}
                </p>
                <p>{review.review_text}</p>
                <small>
                  {review.created_at
                    ? new Date(review.created_at).toLocaleDateString()
                    : ""}
                </small>
              </article>
            ))}

            {reviews.length === 0 && <p>No reviews yet.</p>}
          </div>
        </section>
      </div>
    </>
  );
}

export default EventDetails;
