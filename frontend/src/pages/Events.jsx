import { useEffect, useState } from "react";
import api from "../api";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";

function Events() {
  const navigate = useNavigate();

  const [events, setEvents] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [sort, setSort] = useState("date");

  const fetchEvents = async () => {
    try {
      const response = await api.get("/events", {
        params: {
          search: search || undefined,
          category: category || undefined,
        },
      });

      let data = [...response.data];

      if (sort === "price-low") {
        data.sort(
          (a, b) => a.ticket_price - b.ticket_price
        );
      }

      if (sort === "price-high") {
        data.sort(
          (a, b) => b.ticket_price - a.ticket_price
        );
      }

      if (sort === "date") {
        data.sort(
          (a, b) =>
            new Date(a.event_date) -
            new Date(b.event_date)
        );
      }

      setEvents(data);
    } catch (error) {
      console.error(error);
      alert("Unable to load events");
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [search, category, sort]);

  const getAvailabilityClass = (tickets) => {
    if (tickets === 0) {
      return "sold-out";
    }

    if (tickets <= 10) {
      return "limited";
    }

    return "available";
  };

  const getAvailabilityText = (tickets) => {
    if (tickets === 0) {
      return "Sold Out";
    }

    if (tickets <= 10) {
      return `Only ${tickets} left`;
    }

    return `${tickets} tickets available`;
  };

  return (
    <>
      <Navbar />

      <div className="events-page">

        <div className="events-header">
          <h1>Discover Events</h1>
          <p>
            Find exciting events and book your tickets.
          </p>
        </div>

        <div className="event-filters">

          <input
            type="text"
            placeholder="🔎 Search events..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            <option value="Music">Music</option>
            <option value="Sports">Sports</option>
            <option value="Technology">
              Technology
            </option>
            <option value="Workshop">
              Workshop
            </option>
            <option value="Comedy">Comedy</option>
          </select>

          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="date">
              Sort by Date
            </option>

            <option value="price-low">
              Price: Low to High
            </option>

            <option value="price-high">
              Price: High to Low
            </option>
          </select>

        </div>

        <div className="events-grid">

          {events.length === 0 ? (
            <div className="no-events">

              <div className="no-events-icon">
                🎫
              </div>

              <h2>No events found</h2>

              <p>
                Try another search or category.
              </p>

            </div>
          ) : (
            events.map((event) => (

              <div
                className="event-card"
                key={event.id}
              >

                {event.banner_image ? (
                  <img
                    src={event.banner_image}
                    alt={event.title}
                    className="event-image"
                  />
                ) : (
                  <div className="event-image-placeholder">
                    🎫
                  </div>
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
                        {getAvailabilityText(
                          event.available_tickets
                        )}
                      </span>

                    </div>

                    <button
                      disabled={
                        event.available_tickets === 0
                      }
                      onClick={() =>
                        navigate(
                          `/events/${event.id}`
                        )
                      }
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

      </div>
    </>
  );
}

export default Events;