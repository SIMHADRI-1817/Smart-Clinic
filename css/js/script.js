// ===== Form Handling =====
document.addEventListener('DOMContentLoaded', function() {
    const bookingForm = document.getElementById('bookingForm');
    
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const patientName = document.getElementById('patientName').value;
            const email = document.getElementById('email').value;
            const phone = document.getElementById('phone').value;
            const appointmentDate = document.getElementById('appointmentDate').value;
            const appointmentTime = document.getElementById('appointmentTime').value;
            const doctor = document.getElementById('doctor').value;
            const symptoms = document.getElementById('symptoms').value;
            
            // Validate form
            if (!patientName || !email || !phone || !appointmentDate || !appointmentTime || !doctor) {
                alert('Please fill in all required fields');
                return;
            }
            
            // Store appointment (in real app, this would send to backend)
            const appointment = {
                name: patientName,
                email: email,
                phone: phone,
                date: appointmentDate,
                time: appointmentTime,
                doctor: doctor,
                symptoms: symptoms,
                bookedAt: new Date().toLocaleString()
            };
            
            // Save to localStorage (for demo purposes)
            let appointments = JSON.parse(localStorage.getItem('appointments')) || [];
            appointments.push(appointment);
            localStorage.setItem('appointments', JSON.stringify(appointments));
            
            // Show success message
            bookingForm.style.display = 'none';
            document.getElementById('successMessage').style.display = 'block';
            
            // Redirect to patient dashboard after 2 seconds
            setTimeout(function() {
                window.location.href = 'patient-dashboard.html';
            }, 2000);
        });
    }
});

// ===== Queue Status Update (Simulated) =====
function updateQueueStatus() {
    const queuePosition = document.querySelector('.queue-position');
    const eta = document.querySelector('.eta');
    
    if (queuePosition && eta) {
        // Simulate queue updates every 10 seconds
        setInterval(function() {
            let currentPos = parseInt(queuePosition.textContent);
            let currentEta = parseInt(eta.textContent);
            
            if (currentPos > 1) {
                currentPos--;
                currentEta = Math.max(0, currentEta - 5);
                
                queuePosition.textContent = currentPos;
                eta.textContent = currentEta + ' mins';
            }
        }, 10000);
    }
}

// Call queue update on page load
updateQueueStatus();

// ===== Mark Appointment Actions =====
function markComplete(button) {
    button.closest('tr').querySelector('.status-badge').textContent = 'Completed';
    button.closest('tr').querySelector('.status-badge').className = 'status-badge completed';
    button.disabled = true;
    alert('Appointment marked as completed');
}

function callNext(button) {
    alert('Patient called. Status updated in system.');
    button.disabled = true;
}

function markNoShow(button) {
    button.closest('tr').querySelector('.status-badge').textContent = 'No-Show';
    button.closest('tr').querySelector('.status-badge').className = 'status-badge danger';
    button.disabled = true;
    alert('Appointment marked as no-show');
}

// ===== Add Event Listeners for Buttons =====
document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('button');
    
    buttons.forEach(button => {
        if (button.textContent.includes('Mark Complete')) {
            button.onclick = function() { markComplete(this); };
        } else if (button.textContent.includes('Call Next')) {
            button.onclick = function() { callNext(this); };
        } else if (button.textContent.includes('Mark No-Show')) {
            button.onclick = function() { markNoShow(this); };
        }
    });
});

