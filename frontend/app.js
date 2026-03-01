async function loadEvents() {
    const response = await fetch(`${API_BASE}/api/events`);
    const events = await response.json();
    const API_BASE = window.location.hostname.includes("localhost")
  ? "http://localhost:5000"
  : "https://prime-pass-backend-primepass.2.rahtiapp.fi"; //Allows both local and prod development

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

    const response = await fetch(`${API_BASE}/api/purchase`, {
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

document.addEventListener("DOMContentLoaded", loadEvents);
