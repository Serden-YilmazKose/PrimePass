async function loadEvents() {
    const response = await fetch("/api/events");
    const events = await response.json();

    const container = document.getElementById("events");
    container.innerHTML = "";

    events.forEach(event => {
        const div = document.createElement("div");
        div.className = "event";

        div.innerHTML = `
            <div class="event-title">${event.name}</div>
            <div class="event-info">
                Date: ${event.date}<br>
                Tickets left: ${event.available}
            </div>
            <input type="number" min="1" value="1" id="qty-${event.id}">
            <button data-event-id="${event.id}">
                Buy Ticket
            </button>
        `;

        container.appendChild(div);
    });

    attachPurchaseHandlers();
}

function attachPurchaseHandlers() {
    document.querySelectorAll("button[data-event-id]").forEach(button => {
        button.addEventListener("click", () => {
            const eventId = button.getAttribute("data-event-id");
            purchaseTicket(eventId);
        });
    });
}

async function purchaseTicket(eventId) {
    const qtyInput = document.getElementById(`qty-${eventId}`);
    const quantity = parseInt(qtyInput.value, 10);

    const response = await fetch("/api/purchase", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            event_id: eventId,
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
