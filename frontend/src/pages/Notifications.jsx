
import { useCallback, useEffect, useState } from "react";
import api from "../api";
import Navbar from "../components/Navbar";

function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [readingId, setReadingId] = useState(null);

  const fetchNotifications = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    setErrorMessage("");

    try {
      const [notificationResponse, reminderResponse] = await Promise.all([
        api.get("/notifications"),
        api.get("/notifications/reminders"),
      ]);

      setNotifications(notificationResponse.data);
      setReminders(reminderResponse.data);
    } catch (error) {
      console.error(error);
      setErrorMessage(
        error.response?.data?.detail || "Unable to load notifications."
      );
    } finally {
      if (showLoading) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const markAsRead = async (id) => {
    try {
      setReadingId(id);
      await api.patch(`/notifications/${id}/read`);
      await fetchNotifications(false);
    } catch (error) {
      console.error(error);
      setErrorMessage(
        error.response?.data?.detail ||
          "Unable to mark notification as read."
      );
    } finally {
      setReadingId(null);
    }
  };

  const unreadCount = notifications.filter(
    (notification) =>
      notification.is_read === 0 || notification.is_read === false
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
            <p>Stay updated with your bookings and events.</p>
          </div>

          <div className="notification-count">
            {unreadCount} Unread
          </div>

          <button
            type="button"
            onClick={() => fetchNotifications()}
          >
            🔄 Refresh
          </button>
        </div>

        {errorMessage && (
          <div role="alert" className="notification-error">
            {errorMessage}
            <button
              type="button"
              onClick={() => fetchNotifications()}
            >
              Try Again
            </button>
          </div>
        )}

        {reminders.length > 0 && (
          <section className="reminders-section">
            <div className="section-title">
              <h2>⏰ Upcoming Event Reminders</h2>
              <span>Next 24 hours</span>
            </div>

            {reminders.map((reminder) => (
              <div
                className="reminder-card"
                key={reminder.booking_id}
              >
                <div className="reminder-icon">⏰</div>
                <div>
                  <h3>{reminder.event_title}</h3>
                  <p>{reminder.message}</p>
                  <strong>
                    📅 {new Date(reminder.event_date).toLocaleString()}
                  </strong>
                </div>
              </div>
            ))}
          </section>
        )}

        <section className="notifications-section">
          <div className="section-title">
            <h2>🔔 All Notifications</h2>
          </div>

          {notifications.length === 0 ? (
            <div className="empty-notifications">
              <div>🔔</div>
              <h2>No notifications</h2>
              <p>You're all caught up!</p>
            </div>
          ) : (
            <div className="notification-list">
              {notifications.map((notification) => {
                const isUnread =
                  notification.is_read === 0 ||
                  notification.is_read === false;

                return (
                  <div
                    key={notification.id}
                    className={`notification-card ${
                      isUnread ? "unread" : "read"
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
                          {(notification.notification_type || "NOTIFICATION")
                            .replaceAll("_", " ")}
                        </span>

                        {isUnread && (
                          <span className="unread-badge">NEW</span>
                        )}
                      </div>

                      <h3>{notification.message}</h3>

                      <p>
                        {notification.created_at
                          ? new Date(
                              notification.created_at
                            ).toLocaleString()
                          : ""}
                      </p>

                      {isUnread && (
                        <button
                          className="read-button"
                          disabled={readingId === notification.id}
                          onClick={() => markAsRead(notification.id)}
                        >
                          {readingId === notification.id
                            ? "Updating..."
                            : "✓ Mark as Read"}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </>
  );
}

export default Notifications;
