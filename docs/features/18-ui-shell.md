# 18. UI Shell, Navigation, Theming & Motion

## Overview
The frontend is a single-page React application with public pages (landing, login), an authenticated app shell (sidebar, top bar with search, alerts bell and profile), role-aware navigation, light/dark theming and a consistent motion language.

## Tech stack
| Concern | Technology |
|---|---|
| Build / dev server | **Vite 5** (port 3000; proxies `/api` and `/socket.io`, including WebSockets, to Flask on 5001) |
| UI | **React 18**, **React Router 6** |
| Styling | **Tailwind CSS 3** + PostCSS/Autoprefixer; colours defined as CSS variables (RGB triplets) so every Tailwind colour works with opacity in both themes |
| Motion | **Framer Motion 11**, shared presets in `utils/motion.js` |
| Icons / toasts | **lucide-react**, **react-hot-toast** |
| Container | `frontend/Dockerfile`, `Dockerfile.render`, `compose.yaml` |

## How it works
- **Routing (`App.jsx`):**
  - Public: `/landing`, `/login`.
  - Post-login: `/welcome`, `/face-unlock`, `/face-attendance`.
  - App shell `Layout` for authenticated routes. `ProtectedRoute` redirects unauthenticated users to `/landing`; `adminOnly` / `managerOnly` routes send other roles to `/my-dashboard`. Unknown paths redirect.
- **Layout (`Layout.jsx`):** a sidebar grouped into sections, where a section appears only if the role has at least one item in it. `TopBar.jsx` shows the page title and description, a quick-search over routes, the alerts bell (doc 7) and the profile menu.
- **Theming (`utils/theme.js`, `ThemeToggle.jsx`):** the theme is stored in `localStorage` and applied as a `data-theme` attribute on `<html>`. Tokens in `index.css` define both palettes, and `tailwind.config.js` maps semantic names (`accent`, `danger`, `warn`, `success`, `bg-*`) onto them.
- **Motion (`utils/motion.js`):**
  - Shared `ease` curve; `fadeIn`, `revealIn`, `heroLine` and `panelIn` presets; and a `useHeroParallax` hook that eases scroll/pointer parallax on hero pages.
  - Product pages use springs for interactive state (sliding filter pills via `layoutId`, list re-ordering via `layout`, cross-fades with `AnimatePresence`).
  - `MotionConfig reducedMotion="user"` respects the OS setting.
- **Landing pages:** `LandingPage.jsx` and `CinematicLanding.jsx` present the product. `WelcomePage.jsx` greets the user after login.

## Key files
`frontend/src/App.jsx`, `main.jsx`, `components/Layout.jsx`, `TopBar.jsx`, `SiteHeader.jsx`, `ThemeToggle.jsx`, `ConfirmDialog.jsx`, `utils/theme.js`, `utils/motion.js`, `index.css`, `tailwind.config.js`, `vite.config.js`.
