<p align="center">
  <img src="public/favicon.svg" alt="MAVU Logo" width="80" height="80">
</p>

<h1 align="center">MAVU AI</h1>

<p align="center">
  <strong>Emotional AI Friend for Children</strong>
</p>

<p align="center">
  First emotional AI companion designed specifically for children aged 5-12 years.
  <br>
  Listens, understands emotions, and supports in difficult moments.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#project-structure">Structure</a> •
  <a href="#api-integration">API</a>
</p>

---

## About

MAVU AI is a revolutionary emotional support application for children. Unlike traditional educational apps, MAVU focuses on emotional connection, empathy, and genuine friendship. The app helps children express their feelings, cope with difficult emotions, and feel supported 24/7.

### Key Differentiators

- **Emotional Intelligence** — Recognizes and responds to children's emotions with empathy
- **Voice Interaction** — Natural voice dialogue adapted for children
- **Parent Dashboard** — Insights for parents without invading child's privacy
- **Safety First** — Instant alerts for concerning patterns, COPPA compliant

## Features

- Multi-language support (Russian, English, Uzbek)
- Responsive design for all devices
- Integrated Payme payment system
- Animated UI with glassmorphism design
- SEO optimized with meta tags and sitemap

## Tech Stack

| Category | Technology |
|----------|------------|
| Framework | React 19 |
| Build Tool | Vite 7 |
| Styling | Tailwind CSS 3 |
| Routing | React Router 7 |
| i18n | i18next |
| Testing | Playwright |
| Linting | ESLint 9 |

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/mavu-landing.git

# Navigate to project directory
cd mavu-app

# Install dependencies
npm install

# Start development server
npm run dev
```

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

## Project Structure

```
mavu-app/
├── public/
│   ├── favicon.svg
│   ├── robots.txt
│   ├── site.webmanifest
│   └── screenshots/          # App screenshots
├── src/
│   ├── components/
│   │   ├── layout/           # Header, Footer, Layout
│   │   └── ui/               # Reusable UI components
│   ├── hooks/                # Custom React hooks
│   ├── i18n/
│   │   └── locales/          # Translation files (ru, en, uz)
│   ├── pages/                # Route components
│   │   ├── Home.jsx
│   │   ├── Purchase.jsx
│   │   ├── PaymentResult.jsx
│   │   ├── Success.jsx
│   │   └── ...
│   ├── services/             # API services
│   │   └── paymeApi.js       # Payme integration
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── tests/                    # E2E tests
├── index.html
├── tailwind.config.js
├── vite.config.js
└── package.json
```

## API Integration

### Payme Payment Gateway

The application integrates with MAVU backend API for payment processing:

```
Base URL: https://api.mavu.app
```

#### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/payme/init` | Initialize payment session |
| GET | `/api/v1/payme/status/{id}` | Check transaction status |

#### Payment Flow

1. User clicks "Pay with Payme" on `/purchase`
2. Frontend calls `/api/v1/payme/init`
3. User is redirected to Payme checkout
4. After payment, user returns to `/payment-result`
5. On success, user sees promo code on `/success`

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page with hero, features, pricing |
| `/purchase` | Payment page with Payme integration |
| `/payment-result` | Payment callback handler |
| `/success` | Promo code display after successful payment |
| `/privacy` | Privacy policy |
| `/offer` | Public offer agreement |
| `/contacts` | Contact information |

## Localization

The app supports three languages:
- **Russian** (`ru`) — Default
- **English** (`en`)
- **Uzbek** (`uz`)

Translation files are located in `src/i18n/locales/`.

## Environment

No environment variables required for frontend. API base URL is configured in `src/services/paymeApi.js`.

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

Copyright © 2025 MAVU AI. All rights reserved.

---

<p align="center">
  Made with ❤️ for children's emotional well-being
</p>
