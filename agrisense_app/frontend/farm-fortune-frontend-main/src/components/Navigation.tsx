import { NavLink } from "react-router-dom";
import { Sprout, Home, Zap, Wheat, Settings, LineChart, Droplets, CloudRain } from "lucide-react";

const Navigation = () => {
  const navItems = [
    { to: "/", icon: Home, label: "Home" },
    { to: "/recommend", icon: Zap, label: "Recommend" },
    { to: "/soil-analysis", icon: Sprout, label: "Soil Analysis" },
    { to: "/crops", icon: Wheat, label: "Crops" },
    { to: "/live", icon: Zap, label: "Live" },
    { to: "/irrigation", icon: Droplets, label: "Irrigation" },
    { to: "/harvesting", icon: CloudRain, label: "Harvesting" },
    { to: "/impact", icon: LineChart, label: "Impact" },
    { to: "/admin", icon: Settings, label: "Admin" },
  ];

  return (
    <nav className="bg-card border-b border-border shadow-soft">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-gradient-primary rounded-lg shadow-medium">
              <Sprout className="w-6 h-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">AgriSense</h1>
              <p className="text-xs text-muted-foreground">Smart Farming Platform</p>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex space-x-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
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
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;