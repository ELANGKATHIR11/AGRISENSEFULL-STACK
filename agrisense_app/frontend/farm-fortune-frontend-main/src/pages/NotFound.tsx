import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Home, ArrowLeft, Search } from "lucide-react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname
    );
  }, [location.pathname]);

  const popularPages = [
    { to: "/", label: "Dashboard", icon: Home },
    { to: "/recommend", label: "Recommendations", icon: Search },
    { to: "/soil-analysis", label: "Soil Analysis", icon: Search },
    { to: "/crops", label: "Crops", icon: Search },
  ];

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 via-white to-blue-50">
      <div className="text-center max-w-md px-4">
        {/* 404 Animation */}
        <div className="mb-8">
          <div className="text-8xl font-bold text-green-600 mb-2">404</div>
          <div className="w-24 h-1 bg-green-600 mx-auto rounded-full"></div>
        </div>

        {/* Error Message */}
        <h1 className="text-2xl font-bold text-gray-900 mb-3">Page Not Found</h1>
        <p className="text-gray-600 mb-2">
          Sorry, we couldn't find the page you're looking for.
        </p>
        <p className="text-sm text-gray-500 mb-8">
          The page <code className="bg-gray-100 px-2 py-1 rounded text-xs">{location.pathname}</code> doesn't exist.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center mb-8">
          <Button asChild className="bg-green-600 hover:bg-green-700">
            <Link to="/">
              <Home className="w-4 h-4 mr-2" />
              Go to Dashboard
            </Link>
          </Button>
          <Button variant="outline" onClick={() => window.history.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Go Back
          </Button>
        </div>

        {/* Popular Pages */}
        <div className="text-left">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Popular Pages:</h3>
          <div className="grid grid-cols-2 gap-2">
            {popularPages.map((page) => (
              <Link
                key={page.to}
                to={page.to}
                className="flex items-center space-x-2 p-2 text-sm text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
              >
                <page.icon className="w-4 h-4" />
                <span>{page.label}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
