import React, { useEffect, useState, useMemo } from 'react';

// Logo asset imports
import LogoLight from '@/assets/branding/agrisense_logo.svg';
import LogoDark from '@/assets/branding/agrisense_logo_dark.svg';
import LogoMonochrome from '@/assets/branding/agrisense_logo_monochrome.svg';
import LogoAnimated from '@/assets/branding/agrisense_logo_animated.svg';
import LogoIcon from '@/assets/branding/agrisense_logo_icon.svg';

export type LogoVariant = 'light' | 'dark' | 'monochrome' | 'animated' | 'icon';
export type LogoSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface AgriSenseLogoProps {
  /** Logo variant to display */
  variant?: LogoVariant | 'auto';
  /** Size preset for the logo */
  size?: LogoSize;
  /** Custom width override */
  width?: number;
  /** Custom height override */
  height?: number;
  /** Alternative text for accessibility */
  alt?: string;
  /** Additional CSS classes */
  className?: string;
  /** Whether to animate on hover */
  animateOnHover?: boolean;
  /** Click handler */
  onClick?: () => void;
}

const sizePresets: Record<LogoSize, { width: number; height: number }> = {
  xs: { width: 120, height: 36 },
  sm: { width: 180, height: 54 },
  md: { width: 280, height: 80 },
  lg: { width: 420, height: 120 },
  xl: { width: 560, height: 160 },
};

/**
 * Smart AgriSense Logo Component
 * 
 * Automatically detects system theme and displays appropriate logo variant.
 * Supports manual variant selection, size presets, animations, and accessibility.
 * 
 * @example
 * ```tsx
 * // Auto theme detection
 * <AgriSenseLogo variant="auto" size="md" />
 * 
 * // Manual variant with custom size
 * <AgriSenseLogo variant="dark" width={300} />
 * 
 * // Icon variant with hover animation
 * <AgriSenseLogo variant="icon" size="sm" animateOnHover />
 * 
 * // Animated variant for hero sections
 * <AgriSenseLogo variant="animated" size="lg" />
 * ```
 */
export function AgriSenseLogo({
  variant = 'auto',
  size = 'md',
  width,
  height,
  alt = 'AgriSense - Smart Farming Intelligence',
  className = '',
  animateOnHover = false,
  onClick,
}: AgriSenseLogoProps) {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [resolvedVariant, setResolvedVariant] = useState<LogoVariant>('light');

  // Detect system theme preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleThemeChange = (e: MediaQueryListEvent) => {
      setIsDarkMode(e.matches);
    };

    // Initial check
    setIsDarkMode(mediaQuery.matches);
    
    // Listen for changes
    mediaQuery.addEventListener('change', handleThemeChange);
    
    return () => mediaQuery.removeEventListener('change', handleThemeChange);
  }, []);

  // Check for document theme classes (common theme implementations)
  useEffect(() => {
    const checkDocumentTheme = () => {
      const html = document.documentElement;
      const body = document.body;
      
      // Check common theme class patterns
      const hasThemeDark = html.classList.contains('dark') || 
                          html.classList.contains('theme-dark') ||
                          body.classList.contains('dark') ||
                          body.classList.contains('theme-dark') ||
                          html.getAttribute('data-theme') === 'dark';
      
      setIsDarkMode(hasThemeDark);
    };

    // Initial check
    checkDocumentTheme();

    // Watch for class changes on document
    const observer = new MutationObserver(checkDocumentTheme);
    observer.observe(document.documentElement, { 
      attributes: true, 
      attributeFilter: ['class', 'data-theme'] 
    });
    observer.observe(document.body, { 
      attributes: true, 
      attributeFilter: ['class'] 
    });

    return () => observer.disconnect();
  }, []);

  // Resolve variant based on auto-detection or manual selection
  useEffect(() => {
    if (variant === 'auto') {
      setResolvedVariant(isDarkMode ? 'dark' : 'light');
    } else {
      setResolvedVariant(variant);
    }
  }, [variant, isDarkMode]);

  // Get logo source based on resolved variant
  const getLogoSrc = (logoVariant: LogoVariant): string => {
    switch (logoVariant) {
      case 'dark':
        return LogoDark;
      case 'monochrome':
        return LogoMonochrome;
      case 'animated':
        return LogoAnimated;
      case 'icon':
        return LogoIcon;
      case 'light':
      default:
        return LogoLight;
    }
  };

  // Calculate dimensions
  const dimensions = useMemo(() => {
    if (width && height) {
      return { width, height };
    }
    if (width && !height) {
      // Maintain aspect ratio (420:120 = 3.5:1)
      return { width, height: Math.round(width / 3.5) };
    }
    if (!width && height) {
      // Maintain aspect ratio
      return { width: Math.round(height * 3.5), height };
    }
    // Use size preset
    return sizePresets[size];
  }, [width, height, size]);

  // Build CSS classes
  const logoClasses = [
    'agrisense-logo',
    'transition-all duration-300 ease-in-out',
    animateOnHover && 'hover:scale-105 hover:drop-shadow-lg',
    onClick && 'cursor-pointer',
    className,
  ].filter(Boolean).join(' ');

  return (
    <img
      src={getLogoSrc(resolvedVariant)}
      alt={alt}
      width={dimensions.width}
      height={dimensions.height}
      className={logoClasses}
      onClick={onClick}
      draggable={false}
      loading="eager"
      decoding="async"
      style={{
        maxWidth: '100%',
        height: 'auto',
      }}
    />
  );
}

/**
 * Compact logo icon component for navigation and small spaces
 */
export function AgriSenseIcon({
  size = 'sm',
  className = '',
  ...props
}: Omit<AgriSenseLogoProps, 'variant'>) {
  return (
    <AgriSenseLogo
      variant="icon"
      size={size}
      className={`agrisense-icon ${className}`}
      {...props}
    />
  );
}

/**
 * Animated logo for hero sections and landing pages
 */
export function AgriSenseHeroLogo({
  size = 'lg',
  className = '',
  ...props
}: Omit<AgriSenseLogoProps, 'variant'>) {
  return (
    <AgriSenseLogo
      variant="animated"
      size={size}
      className={`agrisense-hero-logo ${className}`}
      {...props}
    />
  );
}

/**
 * Theme-aware brand header component
 */
interface BrandHeaderProps {
  showIcon?: boolean;
  showTagline?: boolean;
  size?: LogoSize;
  className?: string;
  onLogoClick?: () => void;
}

export function BrandHeader({
  showIcon = true,
  showTagline = false,
  size = 'md',
  className = '',
  onLogoClick,
}: BrandHeaderProps) {
  return (
    <header className={`flex items-center gap-3 ${className}`}>
      {showIcon && (
        <AgriSenseIcon
          size={size === 'xs' ? 'xs' : 'sm'}
          animateOnHover
          onClick={onLogoClick}
        />
      )}
      <div className="flex flex-col">
        <AgriSenseLogo
          variant="auto"
          size={size}
          className="hidden sm:block"
          onClick={onLogoClick}
        />
        {showTagline && (
          <span className="text-xs text-gray-600 dark:text-gray-400 font-medium tracking-wide hidden md:block">
            SMART FARMING INTELLIGENCE
          </span>
        )}
      </div>
    </header>
  );
}

// Hook for logo theme detection
export function useLogoTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const detectTheme = () => {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const hasThemeDark = document.documentElement.classList.contains('dark') ||
                          document.body.classList.contains('dark');
      
      setTheme(hasThemeDark || prefersDark ? 'dark' : 'light');
    };

    detectTheme();
    
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', detectTheme);
    
    const observer = new MutationObserver(detectTheme);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    
    return () => {
      mediaQuery.removeEventListener('change', detectTheme);
      observer.disconnect();
    };
  }, []);

  return theme;
}

export default AgriSenseLogo;