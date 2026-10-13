
import { useEffect, useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";

function Events() {
  const navigate = useNavigate();

  const [events, setEvents] = useState([]);
  const [search, setSearch] = useState("");
  const [location, setLocation] = useState("");
  const [category, setCategory] = useState("");
  const [sort, setSort] = useState("date");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const fetchEvents = async () => {
      setLoading(true);
      setErrorMessage("");

      try {
        const response = await api.get("/events", {
          params: {
            search: search || undefined,
            category: category || undefined,
          },
        });

        let data = [...response.data];

        // Filter by location
        if (location.trim()) {
          data = data.filter((event) =>
            (event.location || "")
              .toLowerCase()
              .includes(location.trim().toLowerCase())
          );
        }

        // Filter by date range
        if (startDate) {
          data = data.filter(
            (event) =>
              new Date(event.event_date) >=
              new Date(`${startDate}T00:00:00`)
          );
        }

        if (endDate) {
          data = data.filter(
            (event) =>
              new Date(event.event_date) <=
              new Date(`${endDate}T23:59:59`)
          );
        }

        // Sorting
        if (sort === "price-low") {
          data.sort(
            (a, b) => Number(a.ticket_price) - Number(b.ticket_price)
          );
        } else if (sort === "price-high") {
          data.sort(
            (a, b) => Number(b.ticket_price) - Number(a.ticket_price)
          );
        } else if (sort === "date") {
          data.sort(
            (a, b) =>
              new Date(a.event_date) - new Date(b.event_date)
          );
        } else if (sort === "popularity") {
          // Popularity is based on confirmed bookings when available.
          data.sort(
            (a, b) =>
              Number(b.booking_count || 0) -
              Number(a.booking_count || 0)
          );
        }

        setEvents(data);
      } catch (error) {
        console.error(error);
        setErrorMessage("Unable to load events. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [search, category, sort, location, startDate, endDate]);

  const clearFilters = () => {
    setSearch("");
    setLocation("");
    setCategory("");
    setSort("date");
    setStartDate("");
    setEndDate("");
  };

  const getAvailabilityClass = (tickets) => {
    if (tickets === 0) return "sold-out";
    if (tickets <= 10) return "limited";
    return "available";
  };

  const getAvailabilityText = (tickets) => {
    if (tickets === 0) return "Sold Out";
    if (tickets <= 10) return `Only ${tickets} left`;
    return `${tickets} tickets available`;
  };

  return (
    <>
      <Navbar />

      <div className="events-page">
        <div className="events-header">
          <h1>Discover Events</h1>
          <p>Find exciting events and book your tickets.</p>
        </div>

        <div className="event-filters">
          <input
            type="text"
            placeholder="🔎 Search by event name or description"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          <input
            type="text"
            placeholder="📍 Search by location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />

          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            <option value="Music">Music</option>
            <option value="Sports">Sports</option>
            <option value="Technology">Technology</option>
            <option value="Workshop">Workshop</option>
            <option value="Comedy">Comedy</option>
          </select>

          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="date">Sort by Date</option>
            <option value="price-low">Price: Low to High</option>
            <option value="price-high">Price: High to Low</option>
            <option value="popularity">Most Popular</option>
          </select>

          <div className="date-filter">
            <label htmlFor="start-date">From</label>
            <input
              id="start-date"
              type="date"
              value={startDate}
              max={endDate || undefined}
              onChange={(e) => setStartDate(e.target.value)}
            />

            <label htmlFor="end-date">To</label>
            <input
              id="end-date"
              type="date"
              value={endDate}
              min={startDate || undefined}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>

          <button type="button" onClick={clearFilters}>
            Clear Filters
          </button>
        </div>

        {errorMessage && (
          <p role="alert">{errorMessage}</p>
        )}

        {loading ? (
          <div className="no-events">Loading events...</div>
        ) : (
          <div className="events-grid">
            {events.length === 0 ? (
              <div className="no-events">
                <div className="no-events-icon">🎫</div>
                <h2>No events found</h2>
                <p>Try changing your search or filters.</p>
              </div>
            ) : (
              events.map((event) => (
                <div className="event-card" key={event.id}>
                  {event.banner_image ? (
                    <img
                      src={event.banner_image}
                      alt={event.title}
                      className="event-image"
                    />
                  ) : (
                    <div className="event-image-placeholder">🎫</div>
                  )}

                  <div className="event-card-content">
                    <span className="event-category">
                      {event.category}
                    </span>

                    <h2>{event.title}</h2>

                    <p className="event-description">
                      {event.description}
                    </p>

                    <div className="event-meta">
                      <p>📍 {event.location}</p>
                      <p>
                        📅{" "}
                        {new Date(event.event_date).toLocaleString()}
                      </p>
                    </div>

                    <div className="event-bottom">
                      <div>
                        <span className="price">
                          ₹{event.ticket_price}
                        </span>

                        <span
                          className={`available ${getAvailabilityClass(
                            event.available_tickets
                          )}`}
                        >
                          {getAvailabilityText(event.available_tickets)}
                        </span>
                      </div>

                      <button
                        disabled={event.available_tickets === 0}
                        onClick={() => navigate(`/events/${event.id}`)}
                      >
                        {event.available_tickets === 0
                          ? "Sold Out"
                          : "View Event"}
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </>
  );
}

export default Events;
