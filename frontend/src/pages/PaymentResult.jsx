import { useLocation, useNavigate, useParams } from "react-router-dom";
import Navbar from "../components/Navbar";

export default function PaymentResult() {
  const { bookingId } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();
  const success = state?.payment_status === "SUCCESS";

  return (
    <>
      <Navbar />
      <main className="details-page">
        <section className="details-card details-content">
          <h1>{success ? "✅ Payment Successful" : "❌ Payment Failed"}</h1>
          <p>Booking: #{bookingId}</p>
          <p>Status: {state?.booking_status || "Unknown"}</p>
          <p>Transaction: {state?.transaction_id || "Not available"}</p>
          <button onClick={() => navigate("/bookings")}>View My Bookings</button>
          <button onClick={() => navigate("/events")}>Browse Events</button>
        </section>
      </main>
    </>
  );
}