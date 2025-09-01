import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navigation from "./components/Navigation";
import { I18nProvider } from "./i18n";
import Home from "./pages/Home";
import Dashboard from "@/pages/Dashboard";
import Recommend from "./pages/Recommend";
import SoilAnalysis from "./pages/SoilAnalysis";
import Crops from "./pages/Crops";
import Admin from "./pages/Admin";
import NotFound from "./pages/NotFound";
import LiveStats from "./pages/LiveStats";
import ImpactGraphs from "./pages/ImpactGraphs";
import Irrigation from "@/pages/Irrigation";
import Harvesting from "@/pages/Harvesting";
import Chatbot from "@/pages/Chatbot";

const queryClient = new QueryClient();

// Use '/ui' only in production when the UI is served by FastAPI under /ui.
// In Vite dev (http://localhost:8080), use root basename to avoid route mismatch.
const routerBasename = import.meta.env.PROD ? "/ui" : "/";

const App = () => (
  <QueryClientProvider client={queryClient}>
    <I18nProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter basename={routerBasename}>
          <div className="min-h-screen bg-background">
            <Navigation />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/recommend" element={<Recommend />} />
              <Route path="/soil-analysis" element={<SoilAnalysis />} />
              <Route path="/crops" element={<Crops />} />
              <Route path="/live" element={<LiveStats />} />
              <Route path="/irrigation" element={<Irrigation />} />
              <Route path="/harvesting" element={<Harvesting />} />
              <Route path="/chat" element={<Chatbot />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="/impact" element={<ImpactGraphs />} />
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </div>
        </BrowserRouter>
      </TooltipProvider>
    </I18nProvider>
  </QueryClientProvider>
);

export default App;
