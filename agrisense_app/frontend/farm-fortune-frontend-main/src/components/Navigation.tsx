import { NavLink } from "react-router-dom";
import { Home, Zap, Wheat, Settings, LineChart, Droplets, CloudRain, MessageSquare, Droplet, Bug, Sprout, Activity, BarChart3, Shield, Scissors, Cpu, Eye, Search } from "lucide-react";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "./LanguageSwitcher";

const Navigation = () => {
  const { t } = useTranslation();
  
  const navItems = [
    { to: "/", icon: Home, label: t("nav_home") },
    { to: "/recommend", icon: Zap, label: t("nav_recommend") },
    { to: "/soil-analysis", icon: Wheat, label: t("nav_soil") },
    { to: "/crops", icon: Sprout, label: t("nav_crops") },
    { to: "/live", icon: Activity, label: "Live Stats" },
    { to: "/irrigation", icon: Droplets, label: "Irrigation" },
    { to: "/tank", icon: Droplet, label: "Tank" },
    { to: "/harvesting", icon: Wheat, label: "Harvesting" },
    { to: "/chat", icon: MessageSquare, label: "Chat" },
    { to: "/disease-management", icon: Shield, label: "Disease Mgmt" },
    { to: "/weed-management", icon: Scissors, label: "Weed Mgmt" },
    { to: "/arduino", icon: Cpu, label: "Arduino" },
    { to: "/impact", icon: BarChart3, label: "Impact" },
    { to: "/admin", icon: Settings, label: "Admin" },
  ];

  return (
    <nav className="bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 shadow-xl border-b border-green-500/20 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Enhanced Logo */}
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white/20 rounded-xl backdrop-blur-sm">
              <Sprout className="w-6 h-6 text-white" />
            </div>
            <div className="text-xl font-bold text-white">
              {t("app_title")}
              <div className="text-xs text-green-100 font-normal">{t("app_tagline")}</div>
            </div>
          </div>

          {/* Enhanced Navigation Links */}
          <div className="flex items-center space-x-1 overflow-x-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center space-x-1 px-3 py-2 rounded-xl font-medium text-xs whitespace-nowrap transition-all duration-200 ${isActive
                    ? "bg-white/20 text-white shadow-lg backdrop-blur-sm border border-white/30"
                    : "text-green-100 hover:text-white hover:bg-white/10 hover:backdrop-blur-sm"
                  }`
                }
              >
                <item.icon className="w-4 h-4 flex-shrink-0" />
                <span className="hidden sm:inline">{item.label}</span>
              </NavLink>
            ))}
            
            {/* Language Switcher */}
            <div className="ml-2">
              <LanguageSwitcher />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;