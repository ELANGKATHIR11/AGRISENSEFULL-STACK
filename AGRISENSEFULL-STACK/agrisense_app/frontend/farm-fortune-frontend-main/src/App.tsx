import { Suspense, lazy } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navigation from "./components/Navigation";
import { I18nProvider } from "./i18n";

// Route-based code splitting (lazy load pages)
const Home = lazy(() => import("./pages/Home"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Recommend = lazy(() => import("./pages/Recommend"));
const SoilAnalysis = lazy(() => import("./pages/SoilAnalysis"));
const Crops = lazy(() => import("./pages/Crops"));
const Admin = lazy(() => import("./pages/Admin"));
const NotFound = lazy(() => import("./pages/NotFound"));
const LiveStats = lazy(() => import("./pages/LiveStats"));
const ImpactGraphs = lazy(() => import("./pages/ImpactGraphs"));
const Irrigation = lazy(() => import("./pages/Irrigation"));
const Harvesting = lazy(() => import("./pages/Harvesting"));
const Chatbot = lazy(() => import("./pages/Chatbot"));
const Tank = lazy(() => import("./pages/Tank"));

// Sensible React Query defaults for perf and UX
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000, // 30s fresh data window
      gcTime: 5 * 60_000, // 5 min cache retention
      retry: 2,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

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
            <Suspense fallback={<div className="p-6 text-sm text-muted-foreground">Loading…</div>}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/recommend" element={<Recommend />} />
                <Route path="/soil-analysis" element={<SoilAnalysis />} />
                <Route path="/crops" element={<Crops />} />
                <Route path="/live" element={<LiveStats />} />
                <Route path="/irrigation" element={<Irrigation />} />
                <Route path="/tank" element={<Tank />} />
                <Route path="/harvesting" element={<Harvesting />} />
                <Route path="/chat" element={<Chatbot />} />
                <Route path="/admin" element={<Admin />} />
                <Route path="/impact" element={<ImpactGraphs />} />
                {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </div>
        </BrowserRouter>
      </TooltipProvider>
    </I18nProvider>
  </QueryClientProvider>
);

export default App;
