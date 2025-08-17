// AGB Communication Attendance Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard functionality
    initializeDashboard();
    
    // Add logout confirmation
    const logoutBtns = document.querySelectorAll('.agb-logout-btn');
    logoutBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to logout?')) {
                e.preventDefault();
            }
        });
    });
});

function initializeDashboard() {
    // Add smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';
    
    // Add loading states to buttons
    const buttons = document.querySelectorAll('.agb-back-btn, .agb-nav-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            this.style.opacity = '0.7';
            this.style.transform = 'scale(0.95)';
        });
    });
    
    // Add loading state to stat cards
    const statCards = document.querySelectorAll('.agb-stat-card');
    statCards.forEach(card => {
        card.addEventListener('click', function() {
            this.style.opacity = '0.8';
            this.style.transform = 'translateY(-3px) scale(0.98)';
        });
    });
    
    // Add hover effects to stat cards
    const statCards = document.querySelectorAll('.agb-stat-card');
    statCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Add click animation to calendar days
    const calendarDays = document.querySelectorAll('.agb-calendar-day');
    calendarDays.forEach(day => {
        day.addEventListener('click', function() {
            if (!this.classList.contains('agb-calendar-day-empty')) {
                this.style.animation = 'pulse 0.3s ease-in-out';
                setTimeout(() => {
                    this.style.animation = '';
                }, 300);
            }
        });
    });
    
    // Add fade-in animation to details cards
    const detailCards = document.querySelectorAll('.agb-detail-card');
    detailCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
    
    // Add responsive table functionality for mobile
    handleMobileResponsiveness();
}

function handleMobileResponsiveness() {
    const handleResize = () => {
        const isMobile = window.innerWidth <= 768;
        const statsGrid = document.querySelector('.agb-stats-grid');
        
        if (statsGrid) {
            if (isMobile) {
                statsGrid.style.gridTemplateColumns = '1fr';
            } else {
                statsGrid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(280px, 1fr))';
            }
        }
    };
    
    window.addEventListener('resize', handleResize);
    handleResize(); // Call once on load
}

// Add CSS for pulse animation
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
`;
document.head.appendChild(style);

// Utility functions for date handling
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
}

function formatTime(dateTimeString) {
    const date = new Date(dateTimeString);
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

// Add smooth transitions for navigation
function navigateWithTransition(url) {
    document.body.style.opacity = '0.7';
    setTimeout(() => {
        window.location.href = url;
    }, 200);
}

// Session management utilities
function checkSession() {
    // This would be handled server-side in Odoo
    // Just for client-side feedback
    const sessionActive = true; // Placeholder
    if (!sessionActive) {
        window.location.href = '/employee/register';
    }
}

// Export functions for global use
window.AttendanceDashboard = {
    formatDate,
    formatTime,
    navigateWithTransition,
    checkSession
};