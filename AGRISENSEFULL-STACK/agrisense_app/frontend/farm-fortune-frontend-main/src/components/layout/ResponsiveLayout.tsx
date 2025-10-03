/**
 * Responsive Layout Components with Accessibility
 * Grid system and layout utilities for AgriSense dashboard
 */
import React, { forwardRef, HTMLAttributes, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Types
interface GridProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  cols?: number | { xs?: number; sm?: number; md?: number; lg?: number; xl?: number };
  gap?: number | string;
  className?: string;
}

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  loading?: boolean;
  error?: string;
  className?: string;
  elevated?: boolean;
  bordered?: boolean;
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  children: ReactNode;
  className?: string;
}

interface TabsProps {
  tabs: Array<{
    id: string;
    label: string;
    content: ReactNode;
    disabled?: boolean;
    badge?: string | number;
  }>;
  defaultTab?: string;
  onChange?: (tabId: string) => void;
  className?: string;
}

// Grid Component with responsive breakpoints
export const ResponsiveGrid = forwardRef<HTMLDivElement, GridProps>(
  ({ children, cols = 1, gap = 4, className = '', ...props }, ref) => {
    let gridClasses = '';

    if (typeof cols === 'number') {
      // Simple grid with fixed columns
      gridClasses = `grid-cols-${Math.min(cols, 12)}`;
    } else {
      // Responsive grid with breakpoint-specific columns
      const { xs = 1, sm = xs, md = sm, lg = md, xl = lg } = cols;
      gridClasses = [
        `grid-cols-${xs}`,
        `sm:grid-cols-${sm}`,
        `md:grid-cols-${md}`,
        `lg:grid-cols-${lg}`,
        `xl:grid-cols-${xl}`,
      ].join(' ');
    }

    const gapClass = typeof gap === 'number' ? `gap-${gap}` : gap;

    return (
      <div
        ref={ref}
        className={`grid ${gridClasses} ${gapClass} ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }
);

ResponsiveGrid.displayName = 'ResponsiveGrid';

// Card Component with loading and error states
export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ 
    children, 
    title, 
    subtitle, 
    actions, 
    loading = false, 
    error, 
    className = '', 
    elevated = false,
    bordered = true,
    ...props 
  }, ref) => {
    const cardClasses = [
      'bg-white rounded-lg overflow-hidden transition-all duration-200',
      elevated ? 'shadow-lg hover:shadow-xl' : 'shadow',
      bordered ? 'border border-gray-200' : '',
      className
    ].filter(Boolean).join(' ');

    if (loading) {
      return (
        <div ref={ref} className={cardClasses} {...props}>
          {(title || subtitle) && (
            <div className="px-6 py-4 border-b border-gray-200">
              {title && (
                <div className="h-6 bg-gray-200 rounded animate-pulse mb-2"></div>
              )}
              {subtitle && (
                <div className="h-4 bg-gray-200 rounded animate-pulse w-2/3"></div>
              )}
            </div>
          )}
          <div className="p-6">
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              <div className="h-4 bg-gray-200 rounded animate-pulse w-5/6"></div>
              <div className="h-4 bg-gray-200 rounded animate-pulse w-4/6"></div>
            </div>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div ref={ref} className={cardClasses} {...props}>
          {(title || subtitle) && (
            <div className="px-6 py-4 border-b border-gray-200">
              {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
              {subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
            </div>
          )}
          <div className="p-6">
            <div className="flex items-center justify-center text-red-600">
              <svg className="h-8 w-8 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.96-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span className="text-sm">{error}</span>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div ref={ref} className={cardClasses} {...props}>
        {(title || subtitle || actions) && (
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div>
              {title && (
                <h3 className="text-lg font-semibold text-gray-900 leading-6">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
              )}
            </div>
            {actions && <div className="flex items-center space-x-2">{actions}</div>}
          </div>
        )}
        <div className="p-6">{children}</div>
      </div>
    );
  }
);

Card.displayName = 'Card';

// Modal Component with accessibility
export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  size = 'md',
  children,
  className = ''
}) => {
  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4'
  };

  // Handle escape key
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Lock body scroll when modal is open
  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={onClose}
          />

          {/* Modal */}
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className={`
                  relative w-full ${sizeClasses[size]} bg-white rounded-lg shadow-xl
                  ${className}
                `}
                role="dialog"
                aria-modal="true"
                aria-labelledby={title ? 'modal-title' : undefined}
              >
                {/* Header */}
                {title && (
                  <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                    <h2
                      id="modal-title"
                      className="text-lg font-semibold text-gray-900"
                    >
                      {title}
                    </h2>
                    <button
                      onClick={onClose}
                      className="text-gray-400 hover:text-gray-600 transition-colors"
                      aria-label="Close modal"
                    >
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                )}

                {/* Content */}
                <div className="px-6 py-4">{children}</div>
              </motion.div>
            </div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
};

// Tabs Component with keyboard navigation
export const Tabs: React.FC<TabsProps> = ({
  tabs,
  defaultTab,
  onChange,
  className = ''
}) => {
  const [activeTab, setActiveTab] = React.useState(defaultTab || tabs[0]?.id);

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
    onChange?.(tabId);
  };

  const handleKeyDown = (e: React.KeyboardEvent, tabId: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleTabChange(tabId);
    }
  };

  const activeTabContent = tabs.find(tab => tab.id === activeTab)?.content;

  return (
    <div className={`w-full ${className}`}>
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs" role="tablist">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && handleTabChange(tab.id)}
              onKeyDown={(e) => !tab.disabled && handleKeyDown(e, tab.id)}
              disabled={tab.disabled}
              role="tab"
              aria-selected={activeTab === tab.id}
              aria-controls={`tabpanel-${tab.id}`}
              className={`
                group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm
                transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500
                ${activeTab === tab.id
                  ? 'border-green-500 text-green-600'
                  : tab.disabled
                  ? 'border-transparent text-gray-400 cursor-not-allowed'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span>{tab.label}</span>
              {tab.badge && (
                <span className={`
                  ml-3 py-0.5 px-2.5 rounded-full text-xs font-medium
                  ${activeTab === tab.id
                    ? 'bg-green-100 text-green-600'
                    : 'bg-gray-100 text-gray-900'
                  }
                `}>
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            id={`tabpanel-${tab.id}`}
            role="tabpanel"
            aria-labelledby={tab.id}
            className={activeTab === tab.id ? 'block' : 'hidden'}
          >
            <AnimatePresence mode="wait">
              {activeTab === tab.id && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  {tab.content}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </div>
  );
};

// Loading Skeleton Component
export const LoadingSkeleton: React.FC<{
  lines?: number;
  className?: string;
}> = ({ lines = 3, className = '' }) => {
  return (
    <div className={`animate-pulse ${className}`}>
      {Array.from({ length: lines }, (_, i) => (
        <div
          key={i}
          className={`h-4 bg-gray-200 rounded mb-3 ${
            i === lines - 1 ? 'w-2/3' : 'w-full'
          }`}
        />
      ))}
    </div>
  );
};

// Error Boundary Component
export class ErrorBoundary extends React.Component<
  { children: ReactNode; fallback?: ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: ReactNode; fallback?: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <svg className="h-8 w-8 text-red-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.96-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div>
                <h3 className="text-sm font-medium text-red-800">Something went wrong</h3>
                <p className="text-sm text-red-700 mt-1">
                  {this.state.error?.message || 'An unexpected error occurred'}
                </p>
              </div>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

// Utility Components
export const Container: React.FC<{
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  className?: string;
}> = ({ children, size = 'xl', className = '' }) => {
  const sizeClasses = {
    sm: 'max-w-2xl',
    md: 'max-w-4xl',
    lg: 'max-w-6xl',
    xl: 'max-w-7xl',
    full: 'max-w-full'
  };

  return (
    <div className={`mx-auto px-4 sm:px-6 lg:px-8 ${sizeClasses[size]} ${className}`}>
      {children}
    </div>
  );
};

export const Section: React.FC<{
  children: ReactNode;
  className?: string;
  id?: string;
}> = ({ children, className = '', id }) => {
  return (
    <section id={id} className={`py-8 ${className}`}>
      {children}
    </section>
  );
};