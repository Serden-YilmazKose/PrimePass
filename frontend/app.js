let currentUserId = null;
const viewedThisPage = new Set();

function showUserProfile(name) {
    document.getElementById("login-container").style.display = "none";
    const profileDiv = document.getElementById("user-profile");
    profileDiv.style.display = "flex";
    document.getElementById("display-name").textContent = `Welcome, ${name}`;
}

async function register() {
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const messageDiv = document.getElementById("message");

    const response = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password })
    });

    const result = await response.json();

    if (response.ok) {
        currentUserId = result.user_id;
        messageDiv.textContent = "Registration successful! You are now logged in.";
        showUserProfile(name || email.split('@')[0]);
    } else {
        messageDiv.textContent = result.error;
    }
}

async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const messageDiv = document.getElementById("message");

    const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });

    const result = await response.json();

    if (response.ok) {
        currentUserId = result.user_id;
        messageDiv.textContent = "Login successful!";
        showUserProfile(email.split('@')[0]);
    } else {
        messageDiv.textContent = result.error;
    }
}

function logout() {
    currentUserId = null;
    viewedThisPage.clear();
    
    document.getElementById("user-profile").style.display = "none";
    document.getElementById("login-container").style.display = "block";
    document.getElementById("message").textContent = "You have been logged out.";
    
    document.getElementById("email").value = "";
    document.getElementById("password").value = "";
    document.getElementById("name").value = "";
}

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
    // Log event view
    const titleEl = div.querySelector(".event-title");
    if (titleEl) {
        titleEl.style.cursor = "pointer";
        titleEl.title = "Click to log view";

        titleEl.addEventListener("click", async () => {
                if (!currentUserId) return;
                if (viewedThisPage.has(event.id)) return;

                viewedThisPage.add(event.id);

                await logActivity(
                    currentUserId,
                    event.id,
                    "view",
                    { source: "ui_event_title_click" }
                );
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

    if (!currentUserId) {
        alert("Please login first.");
        return;
    }

    const qtyInput = document.getElementById(`qty-${ticketId}`);
    const quantity = parseInt(qtyInput.value, 10);

    const response = await fetch("/api/purchase", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: currentUserId,
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

document.addEventListener("DOMContentLoaded", loadEvents);
