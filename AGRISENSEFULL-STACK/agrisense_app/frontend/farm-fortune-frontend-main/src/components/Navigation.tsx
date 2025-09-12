import { NavLink } from "react-router-dom";
import { Home, Zap, Wheat, Settings, LineChart, Droplets, CloudRain, MessageSquare, Droplet } from "lucide-react";
import { useI18n } from "../i18n";

// Lazy-import map to prefetch on hover (use relative paths to avoid alias resolution issues)
const routePrefetchers: Record<string, () => Promise<unknown>> = {
  "/": () => import("../pages/Dashboard"),
  "/recommend": () => import("../pages/Recommend"),
  "/soil-analysis": () => import("../pages/SoilAnalysis"),
  "/crops": () => import("../pages/Crops"),
  "/live": () => import("../pages/LiveStats"),
  "/irrigation": () => import("../pages/Irrigation"),
  "/tank": () => import("../pages/Tank"),
  "/harvesting": () => import("../pages/Harvesting"),
  "/chat": () => import("../pages/Chatbot"),
  "/impact": () => import("../pages/ImpactGraphs"),
  "/admin": () => import("../pages/Admin"),
};

const Navigation = () => {
  const { t } = useI18n();
  const LangTabs = () => {
    const { locale, setLocale } = useI18n();
    const options: { code: "en" | "hi" | "ne"; label: string }[] = [
      { code: "en", label: "EN" },
      { code: "hi", label: "हिंदी" },
      { code: "ne", label: "नेपाली" },
    ];
    return (
      <div className="inline-flex rounded-md border overflow-hidden">
        {options.map((opt, idx) => (
          <button
            key={opt.code}
            type="button"
            onClick={() => setLocale(opt.code)}
            className={`text-xs sm:text-sm px-3 py-1 transition-colors ${
              locale === opt.code
                ? "bg-gradient-primary text-primary-foreground"
                : "bg-card text-foreground hover:bg-secondary"
            } ${idx > 0 ? "border-l" : ""}`}
            title={`Switch to ${opt.label}`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    );
  };
  const navItems = [
    { to: "/", icon: Home, label: t("nav_home") },
    { to: "/recommend", icon: Zap, label: t("nav_recommend") },
    { to: "/soil-analysis", icon: Wheat, label: t("nav_soil") },
    { to: "/crops", icon: Wheat, label: t("nav_crops") },
    { to: "/live", icon: Zap, label: t("nav_live") },
    { to: "/irrigation", icon: Droplets, label: t("nav_irrigation") },
    { to: "/tank", icon: Droplet, label: t("tank") },
    { to: "/harvesting", icon: CloudRain, label: t("nav_harvesting") },
    { to: "/chat", icon: MessageSquare, label: t("nav_chat") },
    { to: "/impact", icon: LineChart, label: t("nav_impact") },
    { to: "/admin", icon: Settings, label: t("nav_admin") },
  ];

  const prefetch = (to: string) => {
    const fn = routePrefetchers[to];
    if (fn) fn().catch(() => {});
  };

  return (
    <nav className="bg-card border-b border-border shadow-soft">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="relative flex items-center justify-center w-10 h-10 rounded-lg shadow-medium logo-pulse overflow-hidden bg-transparent">
              {(() => {
                const im = import.meta as unknown as { env?: { BASE_URL?: string } };
                const base = im?.env?.BASE_URL || "/";
                return (
                <img src={`${base}logo-agrisense-mark-v2.svg`} alt="AgriSense" className="w-10 h-10 select-none" draggable={false} />
                );
              })()}
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">{t("app_title")}</h1>
              <p className="text-xs text-muted-foreground">{t("app_tagline")}</p>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onMouseEnter={() => prefetch(item.to)}
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-300 transform hover:scale-105 ${isActive
                    ? "bg-gradient-primary text-primary-foreground shadow-glow animate-pulse-glow"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary hover:shadow-soft"
                  }`
                }
              >
                <item.icon className="w-4 h-4" />
                <span className="hidden sm:block">{item.label}</span>
              </NavLink>
            ))}
            <div className="ml-2">
              <LangTabs />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;