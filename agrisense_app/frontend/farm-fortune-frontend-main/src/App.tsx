import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navigation from "./components/Navigation";
import Home from "./pages/Home";
import Recommend from "./pages/Recommend";
import SoilAnalysis from "./pages/SoilAnalysis";
import Crops from "./pages/Crops";
import Admin from "./pages/Admin";
import NotFound from "./pages/NotFound";
import LiveStats from "./pages/LiveStats";
import ImpactGraphs from "./pages/ImpactGraphs";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
  <BrowserRouter basename="/ui">
        <div className="min-h-screen bg-background">
          <Navigation />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/recommend" element={<Recommend />} />
            <Route path="/soil-analysis" element={<SoilAnalysis />} />
            <Route path="/crops" element={<Crops />} />
            <Route path="/live" element={<LiveStats />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="/impact" element={<ImpactGraphs />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
