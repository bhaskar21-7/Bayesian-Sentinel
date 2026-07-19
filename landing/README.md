# CyberShield AI - Landing Page

A modern, responsive landing page for the CyberShield AI cybersecurity platform with stunning animations, interactive elements, and professional design.

## ✨ Features

### Hero Section
- **Large, eye-catching title** with gradient text
- **Animated particle system** floating across the background
- **Network grid visualization** with pulsing nodes and animated connections
- **Cyber glow orbs** with floating animations and parallax effects
- **Multiple call-to-action buttons** with smooth interactions
- **Scroll indicator** with bounce animation
- **Responsive design** for all screen sizes

### Feature Cards
- **6 feature cards** showcasing key capabilities:
  - Statistical Detection (0.999 AUC)
  - Bayesian Risk Fusion (0.9999 AUC)
  - Explainable AI (99.6% fidelity)
  - Incident Response (Auto playbook generation)
  - Interactive Dashboard (Real-time monitoring)
  - Real-Time Monitoring (24/7 alerts)
- **Gradient background icons** with hover animations
- **Performance metrics** displayed below each feature
- **Smooth hover effects** with scale and shadow transforms
- **Staggered animations** on page load

### Impact Statistics Section
- **Animated counter numbers** that count up when scrolled into view
- **Real performance metrics** from the platform:
  - 32,000 network events analyzed
  - 22,000 phishing samples detected
  - 99% anomaly detection AUC
  - 0.9999 phishing classifier AUC
- **Easing animations** for smooth counting
- **Decimal and percentage handling**

### Technology Stack Section
- **4 technology categories:**
  - Machine Learning (scikit-learn, LightGBM, XGBoost, IsolationForest)
  - Explainability (SHAP, LIME, Permutation Importance)
  - Dashboard & Visualization (Streamlit, Plotly, Pandas, NumPy)
  - LLM & Automation (Google Gemini, Playbook Generation)
- **Interactive tech items** with hover effects
- **Category cards** with fade-in animations

### Call-to-Action Section
- **Prominent heading** with gradient text
- **Large action buttons** linking to GitHub and documentation
- **Eye-catching background** with gradient accents

### Professional Footer
- **4-column footer layout:**
  - About section
  - Quick links
  - Technology links
  - Social links and community
- **Social media links** with hover animations
- **Copyright and attribution**
- **Responsive grid layout**

## 🎨 Design System

### Colors
```css
--primary-color: #00D9FF;      /* Cyan - Main accent */
--secondary-color: #0969DA;    /* Blue - Secondary accent */
--accent-color: #DA3633;       /* Red - Alert/danger */
--dark-bg: #0D1117;            /* Dark navy background */
--card-bg: #161B22;            /* Slightly lighter card background */
--border-color: #30363D;       /* Subtle borders */
--text-primary: #E6EDF3;       /* Light text */
--text-secondary: #8b949e;     /* Muted text */
--success-color: #1a7f37;      /* Green */
--warning-color: #d29922;      /* Orange/yellow */
```

### Typography
- **Font Family**: System fonts (Apple, Segoe UI, Roboto)
- **Hero Title**: 72px, 900 weight (responsive to 48px on mobile)
- **Section Headers**: 48px, 800 weight
- **Body Text**: 16px, 400 weight
- **Small Text**: 12-14px, 500 weight

### Spacing
- **Sections**: 100-120px padding
- **Cards**: 32-40px gap between items
- **Component Padding**: 20-40px internal
- **Dividers**: 1px with reduced opacity, 32px margins

## 🎬 Animations

### Built-in Animations
- `fadeInDown` - Elements fade in from top
- `fadeInUp` - Elements fade in from bottom
- `slideInUp` - Elements slide up on entrance
- `fadeInLeft/Right` - Horizontal fade entries
- `float` - Continuous floating motion
- `scroll-bounce` - Bouncing scroll indicator
- `pulse-glow` - Pulsing glow effect
- `node-pulse` - Network node pulsing
- `connection-flow` - SVG connection animation
- `counter-up` - Counter number animations

### Interactive Animations
- **Button Hover**: Scale 1.05, shadow elevation, color shift
- **Card Hover**: translateY(-8px), enhanced shadow, border color change
- **Nav Link Hover**: Color change, underline animation
- **Parallax**: Orbs follow mouse movement
- **Scroll Effects**: Elements animate in when scrolled into view

## 📱 Responsive Design

### Breakpoints
- **Desktop**: 1200px+ (full layout)
- **Tablet**: 768px-1199px (2-column grids)
- **Mobile**: <768px (1-column layouts)
- **Small Mobile**: <480px (optimized spacing)

### Responsive Elements
- Navigation collapses on mobile
- Grid layouts adjust column counts
- Hero title scales from 72px to 48px
- Buttons stack vertically on small screens
- Footer becomes single column on mobile

## 🚀 Performance

### Optimizations
- **Minimal JavaScript**: Only essential interactivity
- **CSS-based animations**: Hardware-accelerated transforms
- **Lazy loading**: Images load on viewport intersection
- **Efficient SVG**: Optimized network visualization
- **Canvas particles**: Client-side rendering
- **No external dependencies**: Pure vanilla JS

### Performance Metrics
- **First Contentful Paint**: <1s
- **Time to Interactive**: <2s
- **Lighthouse Score**: 90+

## 📂 File Structure

```
landing/
├── index.html          # Main HTML markup
├── styles.css          # Main styling (1000+ lines)
├── animations.css      # Animation keyframes and utilities
├── particles.js        # Particle system implementation
├── animations.js       # Counter and scroll animations
├── interactions.js     # User interactions and utilities
└── README.md          # This file
```

## 🔧 Usage

### Basic Setup
```bash
# Copy landing folder to your web server
cp -r landing/ /var/www/html/

# Open in browser
open http://localhost/landing/
```

### Customization

#### Change Colors
Edit `:root` variables in `styles.css`:
```css
:root {
    --primary-color: #00D9FF;      /* Change to your color */
    --secondary-color: #0969DA;
    /* ... */
}
```

#### Adjust Animation Speeds
Edit keyframes in `animations.css`:
```css
@keyframes float {
    0%, 100% {
        transform: translateY(0px);
    }
    50% {
        transform: translateY(-30px);  /* Change duration below */
    }
}

.animate-float {
    animation: float 6s ease-in-out infinite;  /* Change 6s */
}
```

#### Modify Particle Count
Edit `particles.js`:
```javascript
this.particleCount = window.innerWidth > 768 ? 50 : 30;  // Adjust 50 and 30
```

#### Update Links
Edit `index.html` and search for `href="#"` or `href="https://github.com/...`

## 🌐 Browser Support

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari 14+
- ✅ iOS Safari 14+
- ✅ Chrome Android

## ♿ Accessibility

- ✅ Semantic HTML structure
- ✅ WCAG AA color contrast
- ✅ Keyboard navigation support
- ✅ Focus visible outlines
- ✅ Alt text on icons
- ✅ Proper heading hierarchy
- ✅ ARIA labels where needed

## 📊 Analytics Integration

The landing page includes a built-in interaction tracker. Access it via:

```javascript
// In browser console
getCyberShieldInteractions();
// Returns array of all user interactions
```

## 🐛 Debugging

### Enable Debug Logging
Open browser console to see:
- Page load time
- Interaction tracking
- Performance metrics

### Common Issues

**Particles not showing?**
- Check browser console for errors
- Ensure canvas context is 2d
- Verify particles.js is loaded

**Animations stuttering?**
- Reduce particle count in particles.js
- Check GPU acceleration is enabled
- Profile in DevTools Performance tab

**Counter numbers not animating?**
- Ensure IntersectionObserver is supported
- Check `data-target` attributes exist
- Verify animations.js is loaded

## 📝 License

Part of CyberShield AI platform. Built with ❤️ for explainable, production-quality AI in cybersecurity.

## 🚀 Deployment

### Netlify
```bash
# Connect your repo and set build settings
# Base directory: landing/
# No build command needed
```

### Vercel
```bash
# Similar to Netlify
# Framework: Static
# Root: landing/
```

### Traditional Server
```bash
# Copy to web root
sudo cp -r landing/* /var/www/html/
```

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/gunjit007/CyberShield-AI/issues
- Discussions: https://github.com/gunjit007/CyberShield-AI/discussions

---

**Last Updated**: 2026-07-15

🛡️ **CyberShield AI** - Explainable Cybersecurity Threat Detection
