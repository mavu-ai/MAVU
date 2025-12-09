import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from './LanguageSwitcher';

export default function Header() {
  const { t } = useTranslation();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const isHome = location.pathname === '/';

  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location]);

  // Prevent scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileMenuOpen]);

  const navLinks = [
    { href: '/#features', label: t('nav.features') },
    { href: '/#screenshots', label: t('nav.app') },
    { href: '/#safety', label: t('nav.safety') },
    { href: '/#pricing', label: t('nav.pricing') },
    { href: '/contacts', label: t('nav.contacts') },
  ];

  const handleNavClick = (e, href) => {
    if (href.startsWith('/#')) {
      if (isHome) {
        e.preventDefault();
        const id = href.replace('/#', '');
        const element = document.getElementById(id);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth' });
        }
      }
    }
    setIsMobileMenuOpen(false);
  };

  return (
    <header className="relative z-50 bg-transparent py-3 md:py-4">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 sm:gap-3 group z-10">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <span className="text-white font-bold text-base sm:text-lg">M</span>
            </div>
            <span className="text-lg sm:text-xl font-bold text-white">MAVU</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-6 xl:gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                onClick={(e) => handleNavClick(e, link.href)}
                className="text-gray-300 hover:text-white transition-colors text-sm font-medium"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="hidden sm:block">
              <LanguageSwitcher />
            </div>

            <Link
              to="/purchase"
              className="hidden md:inline-flex px-4 lg:px-5 py-2 lg:py-2.5 rounded-full bg-gradient-to-r from-violet-600 to-pink-600 text-white text-sm font-semibold hover:opacity-90 transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/30"
            >
              {t('nav.getAccess')}
            </Link>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2 text-gray-300 hover:text-white z-10"
              aria-label="Toggle menu"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {isMobileMenuOpen && (
          <div className="lg:hidden absolute left-0 right-0 top-full bg-dark/95 backdrop-blur-xl animate-fade-in border-t border-white/10">
            <nav className="flex flex-col p-6 gap-2">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  to={link.href}
                  onClick={(e) => handleNavClick(e, link.href)}
                  className="text-gray-200 hover:text-white transition-colors text-lg font-medium py-3 border-b border-white/10"
                >
                  {link.label}
                </Link>
              ))}

              <div className="pt-4 flex flex-col gap-4">
                <div className="sm:hidden">
                  <LanguageSwitcher />
                </div>

                <Link
                  to="/purchase"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="md:hidden w-full py-3 rounded-full bg-gradient-to-r from-violet-600 to-pink-600 text-white text-base font-semibold text-center"
                >
                  {t('nav.getAccess')}
                </Link>
              </div>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
