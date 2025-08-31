function showDayDetails(element) {
    const modal = document.getElementById('day-details-modal');
    const dateElement = document.getElementById('modal-date');
    const shiftElement = document.getElementById('modal-shift');
    const checkinElement = document.getElementById('modal-checkin');
    const checkoutElement = document.getElementById('modal-checkout');
    const lateElement = document.getElementById('modal-late');
    const statusElement = document.getElementById('modal-status');
    const attendanceElement = document.getElementById('modal-attendance');

    const date = element.getAttribute('data-date');
    const checkin = element.getAttribute('data-checkin');
    const checkout = element.getAttribute('data-checkout');
    const late = element.getAttribute('data-late');
    const shift = element.getAttribute('data-shift');
    let status = element.getAttribute('data-status');
    const attendanceFraction = parseFloat(element.getAttribute('data-attendance-fraction') || '1');

    // Handle partial attendance
    if (attendanceFraction === 0.5) {
        status = 'partial';
    }

    if (dateElement) dateElement.textContent = date;
    if (shiftElement) shiftElement.textContent = shift;
    if (checkinElement) checkinElement.textContent = checkin || 'Not recorded';
    if (checkoutElement) checkoutElement.textContent = checkout || 'Not recorded';
    if (lateElement) lateElement.textContent = late + ' minutes';
    if (attendanceElement) attendanceElement.textContent = attendanceFraction.toFixed(1);

    if (statusElement) {
        statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        statusElement.className = 'agb-status-badge agb-status-' + status;
    }

    if (modal) modal.classList.add('show');
}


// Close modal function
function closeDayDetails() {
    const modal = document.getElementById('day-details-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}


// Close modal function
function closeDayDetails() {
    const modal = document.getElementById('day-details-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}


// Close modal function
function closeDayDetails() {
    const modal = document.getElementById('day-details-modal');
    if (modal) modal.classList.remove('show');
}


// Close day details modal
function closeDayDetails() {
    const modal = document.getElementById('day-details-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}

function showLeaveNotification() {
    showNotification('Leave management feature coming soon!', 'info');
}

// Generic notification function
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container') || createNotificationContainer();
    
    const notification = document.createElement('div');
    notification.className = `agb-notification ${type}`;
    notification.textContent = message;
    
    container.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Create notification container if it doesn't exist
function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notification-container';
    container.className = 'agb-notification-container';
    document.body.appendChild(container);
    return container;
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('day-details-modal');
    if (modal && event.target === modal) {
        closeDayDetails();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeDayDetails();
    }
});

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add any initialization code here
    console.log('AGB Attendance Dashboard loaded');
    
    // Add touch support for mobile devices
    if ('ontouchstart' in window) {
        document.body.classList.add('touch-device');
    }
});

// Utility function to format dates
function formatDate(date) {
    const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    return new Date(date).toLocaleDateString('en-US', options);
}

// Utility function to calculate working hours
function calculateWorkingHours(checkin, checkout) {
    if (!checkin || !checkout) return 0;
    
    const checkinTime = new Date('1970-01-01 ' + checkin);
    const checkoutTime = new Date('1970-01-01 ' + checkout);
    
    const diffMs = checkoutTime - checkinTime;
    const diffHours = diffMs / (1000 * 60 * 60);
    
    return Math.max(0, diffHours);
}

(function() {
    let startY = 0;
    let currentY = 0;
    let isPulling = false;
    const threshold = 100; // Pixels to trigger refresh

    // Create refresh icon element if not exists
    let refreshIcon = document.getElementById('pull-refresh-icon');
    if (!refreshIcon) {
        refreshIcon = document.createElement('div');
        refreshIcon.id = 'pull-refresh-icon';
        refreshIcon.innerHTML = '⭮'; // Unicode refresh icon, can use SVG or image
        refreshIcon.style.position = 'fixed';
        refreshIcon.style.top = '10px';
        refreshIcon.style.left = '50%';
        refreshIcon.style.transform = 'translateX(-50%)';
        refreshIcon.style.fontSize = '24px';
        refreshIcon.style.zIndex = '9999';
        refreshIcon.style.display = 'none';
        refreshIcon.style.animation = 'spin 1s linear infinite';
        document.body.appendChild(refreshIcon);
    }

    function touchStartHandler(e) {
        if (window.scrollY === 0) { // Only trigger if at top
            startY = e.touches[0].clientY;
            isPulling = true;
        }
    }

    function touchMoveHandler(e) {
        if (!isPulling) return;
        currentY = e.touches[0].clientY;
        if (currentY - startY > threshold) {
            isPulling = false; // Prevent multiple triggers

            // Show refresh icon
            refreshIcon.style.display = 'block';

            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    }

    function touchEndHandler() {
        isPulling = false;
    }

    document.addEventListener('touchstart', touchStartHandler, {passive: true});
    document.addEventListener('touchmove', touchMoveHandler, {passive: true});
    document.addEventListener('touchend', touchEndHandler);
})();


// Export functions for use in other scripts
window.showDayDetails = showDayDetails;
window.closeDayDetails = closeDayDetails;
window.showLeaveNotification = showLeaveNotification;
window.showNotification = showNotification;