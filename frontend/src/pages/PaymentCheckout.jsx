import { useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import api from "../api";
import Navbar from "../components/Navbar";

export default function PaymentCheckout() {
  const { bookingId } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const pay = async (simulate_success) => {
    setLoading(true);
    try {
      const response = await api.post(`/payments/${bookingId}`, {
        payment_method: "SIMULATED",
        simulate_success,
      });
      navigate(`/payment-result/${bookingId}`, { state: response.data });
    } catch (error) {
      alert(error.response?.data?.detail || "Payment failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <main className="details-page">
        <section className="details-card details-content">
          <h1>Secure Checkout</h1>
          <p>Booking #{bookingId}</p>
          <p>Event: {state?.event_title || "Your event"}</p>
          <p>Tickets: {state?.ticket_count ?? "See booking details"}</p>
          <p>Subtotal: ₹{state?.total_amount ?? "—"}</p>
          <p>Discount: ₹{state?.discount_amount ?? 0}</p>
          <h2>Pay: ₹{state?.final_amount ?? "—"}</h2>
          <p>This is a payment simulation, not a real charge.</p>
          <button disabled={loading} onClick={() => pay(true)}>
            {loading ? "Processing..." : "Simulate Successful Payment"}
          </button>
          <button disabled={loading} onClick={() => pay(false)}>
            Simulate Failed Payment
          </button>
        </section>
      </main>
    </>
  );
}