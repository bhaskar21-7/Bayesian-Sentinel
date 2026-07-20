/**
 * Interactive Elements and Utilities
 */

// Handle keyboard navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        // Close any modals or overlays if needed
        console.log('Escape pressed');
    }
});

// Track page visibility
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('Page hidden');
    } else {
        console.log('Page visible');
    }
});

// Performance monitoring
window.addEventListener('load', () => {
    if (window.performance && window.performance.timing) {
        const perfData = window.performance.timing;
        const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
        console.log('Page load time:', pageLoadTime, 'ms');
    }
});

// Add active state to nav links based on scroll position
function updateActiveNavLink() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');
    
    let current = '';
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        
        if (scrollY >= sectionTop - 200) {
            current = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').substring(1) === current) {
            link.classList.add('active');
            link.style.color = '#00D9FF';
        } else {
            link.style.color = '';
        }
    });
}

window.addEventListener('scroll', updateActiveNavLink);

// Lazy loading for images
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                }
                imageObserver.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

// Accessibility enhancements
function enhanceAccessibility() {
    // Add focus visible styles
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            document.body.classList.add('using-keyboard');
        }
    });
    
    document.addEventListener('mousedown', () => {
        document.body.classList.remove('using-keyboard');
    });
}

enhanceAccessibility();

// Add CSS for keyboard focus
const a11yStyle = document.createElement('style');
a11yStyle.textContent = `
    body.using-keyboard .btn:focus,
    body.using-keyboard .nav-link:focus,
    body.using-keyboard a:focus {
        outline: 2px solid #00D9FF;
        outline-offset: 2px;
    }
`;
document.head.appendChild(a11yStyle);

// Track user interactions for analytics
class UserInteractionTracker {
    constructor() {
        this.interactions = [];
        this.init();
    }
    
    init() {
        document.addEventListener('click', (e) => {
            this.trackInteraction('click', e.target);
        });
        
        document.addEventListener('scroll', () => {
            this.trackInteraction('scroll', window.scrollY);
        });
    }
    
    trackInteraction(type, target) {
        const interaction = {
            type: type,
            target: target.className || target,
            timestamp: new Date().toISOString()
        };
        
        this.interactions.push(interaction);
        
        // Keep only last 50 interactions
        if (this.interactions.length > 50) {
            this.interactions.shift();
        }
    }
    
    getInteractions() {
        return this.interactions;
    }
}

const tracker = new UserInteractionTracker();

// Provide developer access to tracking data
window.getBayesianSentinelInteractions = () => {
    return tracker.getInteractions();
};

console.log('%c🛡️ Bayesian Sentinel - Landing Page', 'color: #00D9FF; font-size: 16px; font-weight: bold;');
console.log('%cInteractive elements initialized', 'color: #8b949e; font-size: 12px;');
console.log('%cTip: Use getBayesianSentinelInteractions() to see user interactions', 'color: #00D9FF; font-size: 12px;');