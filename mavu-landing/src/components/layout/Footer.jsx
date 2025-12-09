import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="relative pt-10 md:pt-12 pb-8 md:pb-10">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 sm:gap-3 group">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <span className="text-white font-bold text-base sm:text-lg">M</span>
            </div>
            <span className="text-lg sm:text-xl font-bold text-white">MAVU</span>
          </Link>

          {/* Links */}
          <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 text-sm text-gray-400">
            <Link to="/privacy" className="hover:text-white transition-colors">
              {t('footer.privacy')}
            </Link>
            <Link to="/offer" className="hover:text-white transition-colors">
              {t('footer.offer')}
            </Link>
            <Link to="/contacts" className="hover:text-white transition-colors">
              {t('footer.contacts')}
            </Link>
            <a
              href="https://t.me/mavuai_bot"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 hover:text-white transition-colors"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
              </svg>
              Telegram
            </a>
          </div>

          {/* Copyright */}
          <p className="text-xs sm:text-sm text-gray-500 text-center">{t('footer.copyright')}</p>
        </div>
      </div>
    </footer>
  );
}
