import { useEffect, useState } from "react";
import api from "../api";
import Navbar from "../components/Navbar";

function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchNotifications = async () => {
    try {
      const [
        notificationResponse,
        reminderResponse,
      ] = await Promise.all([
        api.get("/notifications"),
        api.get("/notifications/reminders"),
      ]);

      setNotifications(notificationResponse.data);
      setReminders(reminderResponse.data);

    } catch (error) {
      console.error(error);
      alert("Unable to load notifications");

    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const markAsRead = async (id) => {
    try {
      await api.patch(
        `/notifications/${id}/read`
      );

      fetchNotifications();

    } catch (error) {
      console.error(error);
      alert("Unable to mark notification as read");
    }
  };

  const unreadCount = notifications.filter(
    (notification) =>
      notification.is_read === 0
  ).length;

  if (loading) {
    return (
      <>
        <Navbar />

        <div className="notifications-loading">
          Loading notifications...
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />

      <div className="notifications-page">

        <div className="notifications-header">

          <div>
            <h1>Notifications</h1>

            <p>
              Stay updated with your bookings and events.
            </p>
          </div>

          <div className="notification-count">
            {unreadCount} Unread
          </div>

        </div>

        {reminders.length > 0 && (
          <section className="reminders-section">

            <div className="section-title">

              <h2>
                ⏰ Upcoming Event Reminders
              </h2>

              <span>
                Next 24 hours
              </span>

            </div>

            {reminders.map((reminder) => (
              <div
                className="reminder-card"
                key={reminder.booking_id}
              >

                <div className="reminder-icon">
                  ⏰
                </div>

                <div>

                  <h3>
                    {reminder.event_title}
                  </h3>

                  <p>
                    {reminder.message}
                  </p>

                  <strong>
                    📅{" "}
                    {new Date(
                      reminder.event_date
                    ).toLocaleString()}
                  </strong>

                </div>

              </div>
            ))}

          </section>
        )}

        <section className="notifications-section">

          <div className="section-title">

            <h2>
              🔔 All Notifications
            </h2>

          </div>

          {notifications.length === 0 ? (

            <div className="empty-notifications">

              <div>🔔</div>

              <h2>
                No notifications
              </h2>

              <p>
                You're all caught up!
              </p>

            </div>

          ) : (

            <div className="notification-list">

              {notifications.map(
                (notification) => (

                  <div
                    key={notification.id}
                    className={`notification-card ${
                      notification.is_read === 0
                        ? "unread"
                        : "read"
                    }`}
                  >

                    <div className="notification-icon">

                      {notification.notification_type ===
                      "BOOKING_CONFIRMED"
                        ? "🎟️"
                        : "🔔"}

                    </div>

                    <div className="notification-content">

                      <div className="notification-top">

                        <span className="notification-type">
                          {notification.notification_type.replaceAll(
                            "_",
                            " "
                          )}
                        </span>

                        {notification.is_read === 0 && (
                          <span className="unread-badge">
                            NEW
                          </span>
                        )}

                      </div>

                      <h3>
                        {notification.message}
                      </h3>

                      <p>
                        {new Date(
                          notification.created_at
                        ).toLocaleString()}
                      </p>

                      {notification.is_read === 0 && (
                        <button
                          className="read-button"
                          onClick={() =>
                            markAsRead(
                              notification.id
                            )
                          }
                        >
                          ✓ Mark as Read
                        </button>
                      )}

                    </div>

                  </div>

                )
              )}

            </div>
          )}

        </section>

      </div>
    </>
  );
}

export default Notifications;