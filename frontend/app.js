const USER_ID = "00000000-0000-0000-0000-000000000001"; // TODO: replace with real logged-in user_id later
const viewedThisPage = new Set();

async function logActivity(userId, eventId, action, meta = null) {
  try {
    await fetch("/api/activity", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        event_id: eventId,
        action: action,
        meta: meta
      })
    });
  } catch (e) {
    console.warn("Activity logging failed:", e);
  }
}

async function loadEvents() {
    const response = await fetch("/api/events");
    const events = await response.json();

    const container = document.getElementById("events");
    container.innerHTML = "";

    events.forEach(event => {
        const div = document.createElement("div");
        div.className = "event";

        // Create ticket type boxes
        let ticketBoxes = "";

        if (event.tickets && event.tickets.length > 0) {
            event.tickets.forEach(ticket => {
                ticketBoxes += `
                    <div class="ticket-box">
                        <strong>${ticket.name}</strong><br>
                        Price: €${ticket.price}<br>
                        Remaining: ${ticket.remaining}<br>
                        <input type="number" min="1" value="1"
                            id="qty-${ticket.id}">
                        <button data-ticket-id="${ticket.id}">
                            Buy
                        </button>
                    </div>
                `;
            });
        } else {
            ticketBoxes = "<div>No tickets available</div>";
        }

        div.innerHTML = `
            <div class="event-title">${event.title}</div>
            <div class="event-info">
                Date: ${new Date(event.starts_at).toLocaleString()}<br>
            </div>
            <div class="ticket-container">
                ${ticketBoxes}
            </div>
        `;

        const titleEl = div.querySelector(".event-title");
    if (titleEl) {
      titleEl.style.cursor = "pointer";
      titleEl.title = "Click to log view";
      titleEl.addEventListener("click", async () => {
        if (viewedThisPage.has(event.id)) return;
        viewedThisPage.add(event.id);

        await logActivity(USER_ID, event.id, "view", { source: "ui_event_title_click" });

        //const messageDiv = document.getElementById("message");
        //messageDiv.textContent = `View logged for "${event.title}"`;
      });
    }

        container.appendChild(div);
    });

    attachPurchaseHandlers();
}

function attachPurchaseHandlers() {
    document.querySelectorAll("button[data-ticket-id]").forEach(button => {
        button.addEventListener("click", () => {
            const ticketId = button.getAttribute("data-ticket-id");
            purchaseTicket(ticketId);
        });
    });
}

async function purchaseTicket(ticketId) {
    const qtyInput = document.getElementById(`qty-${ticketId}`);
    const quantity = parseInt(qtyInput.value, 10);

    const response = await fetch("/api/purchase", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: "00000000-0000-0000-0000-000000000001",  //NEEDS TO BE UPDATED, CURRENTLY TAKES THIS FROM populate_db.py
            ticket_id: ticketId,
            quantity: quantity
        })
    });

    const result = await response.json();
    const messageDiv = document.getElementById("message");

    if (response.ok) {
        messageDiv.textContent = "Purchase successful!";
        loadEvents();
    } else {
        messageDiv.textContent = result.error || "Purchase failed.";
    }
}

async function loadRecommendations(userId) {
    try {
        const response = await fetch(`/api/recommendations/${userId}`);
        const events = await response.json();

        const container = document.getElementById("recommendations");
        container.innerHTML = "";

        events.forEach(event => {
            const div = document.createElement("div");
            div.className = "event";
            div.innerHTML = `
                <div class="event-title">${event.title}</div>
                <div class="event-info">
                    ${event.venue}, ${event.city}<br>
                    ${new Date(event.starts_at).toLocaleString()}
                </div>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.warn("Failed to load recommendations:", e);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadEvents();
    loadRecommendations(USER_ID);
});
